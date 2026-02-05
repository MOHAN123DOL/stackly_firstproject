from jobseeker.models import UserAppliedJob

def can_user_chat(user, job):
    return UserAppliedJob.objects.filter(
        user=user,
        job=job
    ).exists()
