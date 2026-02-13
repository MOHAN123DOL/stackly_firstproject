from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now, timedelta
from jobseeker.models import Company , Job , JobSeeker

class Employee(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="employee_profile"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="employees"
    )
    designation = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.company_name}"



class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"{self.user.username} - {self.otp}"

class Interview(models.Model):

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    MODE_CHOICES = [
        ("online", "Online"),
        ("offline", "Offline"),
    ]

    jobseeker = models.ForeignKey(
        JobSeeker,
        on_delete=models.CASCADE,
        related_name="interviews"
    )

    job = models.ForeignKey(
        Job,  # change if your app name different
        on_delete=models.CASCADE,
        related_name="interviews"
    )

    scheduled_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="scheduled_interviews"
    )

    interview_date = models.DateTimeField()

    mode = models.CharField(
        max_length=10,
        choices=MODE_CHOICES
    )

    meeting_link = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.jobseeker.user.username} - {self.job.title}"