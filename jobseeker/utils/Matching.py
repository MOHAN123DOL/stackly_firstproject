from django.db.models import Q
from jobseeker.models import Job


def match_jobs(alert):
    locations = [l.strip() for l in alert.locations.split(",") if l.strip()]

    return (
        Job.objects
        .select_related("company") 
        .filter(
            role__icontains=alert.role,
            duration=alert.duration,
            salary_max__gte=alert.min_salary,
            salary_min__lte=alert.max_salary,
            company__location__iregex=r"|".join(locations) if locations else None,
        )
    )