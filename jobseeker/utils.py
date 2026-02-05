from django.db.models import Q
from .models import Job


def match_jobs(alert):
    locations = [l.strip() for l in alert.locations.split(",")]

    location_q = Q()
    for loc in locations:
        location_q |= Q(company__location__icontains=loc)

    return Job.objects.filter(
        role__icontains=alert.role,
        duration=alert.duration,
        salary_min__gte=alert.min_salary,
        salary_max__lte=alert.max_salary,
    ).filter(location_q)


