from django.db.models import Count, Q
from jobseeker.models import Job, JobRecommendationFeedback, Skill
from .total_experiences_calculator import calculate_total_experience


def generate_recommendations(user):
    preference = getattr(user, "preferences", None)
    if not preference:
        return []

    preferred_skills = preference.preferred_skills.all()
    total_skills = preferred_skills.count()

    queryset = Job.objects.all().annotate(
        matched_skills=Count(
            "skills_required",
            filter=Q(skills_required__in=preferred_skills),
            distinct=True
        )
    )

    # Exclude hidden jobs
    queryset = queryset.exclude(
        recommendation_feedbacks__user=user,
        recommendation_feedbacks__feedback_type="HIDE"
    )

    feedback_map = {
        fb.job_id: fb
        for fb in JobRecommendationFeedback.objects.filter(user=user)
    }

    liked_jobs = JobRecommendationFeedback.objects.filter(
        user=user,
        feedback_type="LIKE"
    ).values_list("job_id", flat=True)

    liked_skills = Skill.objects.filter(
        jobs__id__in=liked_jobs
    ).distinct()

    jobseeker = getattr(user, "jobseeker", None)
    total_experience = calculate_total_experience(jobseeker) if jobseeker else 0

    jobs_with_score = []

    for job in queryset:
        score = 0

        # Skill Score
        if total_skills > 0:
            score += (job.matched_skills / total_skills) * 40

        # Salary Score
        if (
            preference.expected_salary_min is not None and
            preference.expected_salary_max is not None and
            job.salary_min is not None and
            job.salary_max is not None
        ):
            if (
                job.salary_max >= preference.expected_salary_min and
                job.salary_min <= preference.expected_salary_max
            ):
                score += 20

        # Location Score
        job_location = getattr(job.company, "location", None)
        if preference.preferred_location and job_location:
            if preference.preferred_location.strip().lower() == job_location.strip().lower():
                score += 20

        # Experience Score
        if job.min_experience is not None:
            if total_experience >= job.min_experience:
                score += 20

        # Feedback Adjustment
        feedback = feedback_map.get(job.id)
        if feedback:
            if feedback.feedback_type == "LIKE":
                score += 15
            elif feedback.feedback_type == "DISLIKE":
                score -= 20
            elif feedback.feedback_type == "NOT_RELEVANT":
                score -= 30

            if feedback.rating:
                score += feedback.rating * 2

        # Similar Skill Boost
        if job.skills_required.filter(id__in=liked_skills).exists():
            score += 10

        job.total_score = max(round(score, 2), 0)
        jobs_with_score.append(job)

    jobs_with_score.sort(key=lambda x: x.total_score, reverse=True)

    return jobs_with_score