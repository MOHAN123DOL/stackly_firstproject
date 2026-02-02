from django.db import models

class LandingChoice(models.Model):
    ROLE_CHOICES = (
        ("jobseeker", "Job Seeker"),
        ("employer", "Employer"),
        ("consultant", "Consultant"),
    )

    role = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    redirect_url = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class InfoCard(models.Model):
    key = models.CharField(
        max_length=50,
        unique=True,
        help_text="jobs / jobseekers / employers"
    )
    title = models.CharField(max_length=100)
    icon = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
