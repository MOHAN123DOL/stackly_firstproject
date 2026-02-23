from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from jobseeker.models import JobSeeker , UserAppliedJob , Job ,UserSavedJob , Company , JobExperience, Skill
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache
from .models import Job, JobseekerPreference
from .utils.cache import clear_all_recommendation_cache , clear_user_recommendation_cache



@receiver(post_save, sender=JobseekerPreference)
def preference_saved(sender, instance, **kwargs):
    """
    When preference is updated,
    clear that user's recommendation cache.
    """
    clear_user_recommendation_cache(instance.user.id)


@receiver(post_delete, sender=JobseekerPreference)
def preference_deleted(sender, instance, **kwargs):
    """
    If preference deleted,
    clear that user's cache.
    """
    clear_user_recommendation_cache(instance.user.id)


@receiver(m2m_changed, sender=JobseekerPreference.preferred_skills.through)
def preference_skills_changed(sender, instance, **kwargs):
    """
    If preferred skills added/removed,
    clear that user's cache.
    """
    clear_user_recommendation_cache(instance.user.id)


# Job Signals


@receiver(post_save, sender=Job)
def job_saved(sender, instance, **kwargs):
    """
    When job is created or updated,
    clear all recommendation caches.
    (Because many users may be affected)
    """
    clear_all_recommendation_cache()


@receiver(post_delete, sender=Job)
def job_deleted(sender, instance, **kwargs):
    """
    When job is deleted,
    clear all recommendation caches.
    """
    clear_all_recommendation_cache()


@receiver(m2m_changed, sender=Job.skills_required.through)
def job_skills_changed(sender, instance, **kwargs):
    """
    If job skills change,
    clear all recommendation caches.
    """
    clear_all_recommendation_cache()


