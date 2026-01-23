from django.db import models
from django.contrib.auth.models import User

class JobSeeker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    education = models.TextField(blank=True)
    experience = models.TextField(blank=True)

    def __str__(self):
        return self.user.username
    



class UserAppliedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job_id = models.IntegerField()  # fake / external job reference
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} applied to job {self.job_id}"
    
class UserSavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job_id = models.IntegerField()  # fake / external job reference
    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} saved job {self.job_id}"

