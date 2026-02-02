from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from jobseeker.models import Job
from jobseeker.models import JobSeeker
from django.contrib.auth.models import User


@receiver([post_save, post_delete], sender=Job)
def clear_job_cache(sender, **kwargs):
    cache.delete("infocard_count_jobs")


@receiver([post_save, post_delete], sender=JobSeeker)
def clear_jobseeker_cache(sender, **kwargs):
    cache.delete("infocard_count_jobseekers")


@receiver([post_save, post_delete], sender=User)
def clear_employer_cache(sender, instance, **kwargs):
    if instance.is_staff:
        cache.delete("infocard_count_employers")
