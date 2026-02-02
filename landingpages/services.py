from django.core.cache import cache
from django.contrib.auth.models import User
from jobseeker.models import JobSeeker
from jobseeker.models import Job

CACHE_TIMEOUT = 300 #5min


def get_infocard_count(key):
    cache_key = f"infocard_count_{key}"
    value = cache.get(cache_key)

    if value is not None:
        return value

    if key == "jobs":
        value = Job.objects.count()
    elif key == "jobseekers":
        value = User.objects.filter(is_staff=False).count()
    elif key == "employers":
        value = User.objects.filter(is_staff=True).count()
    else:
        value = 0

    cache.set(cache_key, value, CACHE_TIMEOUT)
    return value
