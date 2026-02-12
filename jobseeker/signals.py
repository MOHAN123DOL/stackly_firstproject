from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from jobseeker.models import JobSeeker , UserAppliedJob , Job ,UserSavedJob , Company , JobExperience, Skill
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache

#oppurtunity overview

@receiver(post_save, sender=JobSeeker)
def clear_recommended_jobs_cache(sender, instance, **kwargs):
    cache_key = f"recommended_jobs_user_{instance.user_id}"
    cache.delete(cache_key)


@receiver(post_save, sender=UserAppliedJob)
def clear_applied_jobs_cache(sender, instance, **kwargs):
    cache_key = f"applied_jobs_user_{instance.user_id}"
    cache.delete(cache_key)

@receiver(post_save, sender=UserSavedJob)
def clear_saved_jobs_cache(sender, instance, **kwargs):
    cache_key = f"saved_jobs_user_{instance.user_id}"
    cache.delete(cache_key)


@receiver(post_save, sender=Company)
def clear_total_companies_cache(sender, instance, **kwargs):
    cache.delete("jobseeker_overview_company")

@receiver(post_save, sender=Job)
def clear_total_jobs_cache(sender, instance, **kwargs):
   cache.delete("jobseeker_overview_jobs")


