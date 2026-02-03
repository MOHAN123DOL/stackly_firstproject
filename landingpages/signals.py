from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from jobseeker.models import JobSeeker, UserAppliedJob, UserSavedJob


# 🔥 JobSeeker profile update (title change, etc.)
@receiver(post_save, sender=JobSeeker)
def clear_overview_on_jobseeker_update(sender, instance, **kwargs):
    cache.delete(f"jobseeker_overview_{instance.user_id}")


# 🔥 Apply / withdraw job
@receiver([post_save, post_delete], sender=UserAppliedJob)
def clear_overview_on_apply(sender, instance, **kwargs):
    cache.delete(f"jobseeker_overview_{instance.user_id}")


# 🔥 Save / unsave job
@receiver([post_save, post_delete], sender=UserSavedJob)
def clear_overview_on_save(sender, instance, **kwargs):
    cache.delete(f"jobseeker_overview_{instance.user_id}")
