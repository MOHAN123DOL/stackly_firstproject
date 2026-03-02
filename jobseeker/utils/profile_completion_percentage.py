from jobseeker.models import JobSeeker


def calculate_profile_completion(user):
    jobseeker, _ = JobSeeker.objects.get_or_create(user=user)

    sections = {
        "first_name": bool(jobseeker.first_name),
        "last_name": bool(jobseeker.last_name),
        "education": bool(jobseeker.education),
        "title": bool(jobseeker.title),
        "avatar": bool(jobseeker.avatar),
        "resume": bool(jobseeker.resume),
        "skills": jobseeker.skills.exists(),
        "experience": jobseeker.experiences.exists(),
    }

    total = len(sections)
    filled = sum(sections.values())
    percentage = round((filled / total) * 100)

    missing = [field for field, status in sections.items() if not status]

    return {
        "completion_percentage": f"{percentage}%",
        "total_fields": total,
        "filled_fields": filled,
        "missing_fields": missing,
    }