from .models import JobSeeker , Job, UserAppliedJob , UserSavedJob , Company
from django.core.cache import cache

from celery import shared_task
from django.core.cache import cache
from .models import JobSeeker
from .utils.total_experiences_calculator import calculate_total_experience

cache_timeout = 300
def get_opportunities_overview(user):
    cache_key = f"jobseeker_overview_{user.id}"
    cached_data = cache.get(cache_key)

    if cached_data:
        return cached_data

    jobseeker = JobSeeker.objects.get(user=user)

    # Default values
    recommended_jobs = []
    recommended_message = None

    # 🔥 Recommended jobs logic
    if not jobseeker.title:
        recommended_message = "Please add your role in your profile"
    else:
        recommended_message = f'For your Job Title {jobseeker.title} '
        qs = Job.objects.filter(
        role__icontains=jobseeker.title
        ).select_related("company").order_by("-posted_on")[:5]

        recommended_jobs = list(
            qs.values(
                "id",
                "role",
                "company__name",
                "posted_on"
            )
        )
    

    data = {
        "total_jobs": Job.objects.count(),
        "total_companies": Company.objects.count(),
        "applied_jobs": UserAppliedJob.objects.filter(user=user).count(),
        "saved_jobs": UserSavedJob.objects.filter(user=user).count(),

        "recommended_message": recommended_message,
        "recommended_count": len(recommended_jobs),
        "recommended_jobs": recommended_jobs,
    }

    cache.set(cache_key, data, cache_timeout)
    return data




