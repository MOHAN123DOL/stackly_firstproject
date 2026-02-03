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
    title = models.CharField(max_length=200,blank=True) 
    experience = models.TextField(blank=True)


    def __str__(self):
        return self.user.username
# models.py
class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)
    location = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    company_logo = models.ImageField(
        upload_to="company_logos/",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True,blank=True)

    def __str__(self):
        return self.name
    
class Job(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="jobs"
    )
    role = models.CharField(max_length=200)
    salary = models.CharField(max_length=100)
    duration = models.CharField(
        max_length=50,
        help_text="Full-time / Internship / Contract"
    )
    posted_on = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.role} at {self.company.name}"



class UserAppliedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    
class UserSavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True)
    saved_at = models.DateTimeField(auto_now_add=True)









