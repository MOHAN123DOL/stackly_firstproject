from django.db import models
from django.contrib.auth.models import User


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class JobSeeker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    resume = models.FileField(upload_to="resumes/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name="jobseekers"
    )
    education = models.TextField(blank=True)
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Desired job role (e.g. Backend Developer)"
    )



    def __str__(self):
        return self.user.username


class JobExperience(models.Model):
    jobseeker = models.ForeignKey(
        JobSeeker,
        on_delete=models.CASCADE,
        related_name="experiences"
    )

    company_name = models.CharField(max_length=200)
    role = models.CharField(max_length=200)

    start_date = models.DateField()
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Leave empty if currently working"
    )

    is_current = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_name} - {self.role}"



class JobAlert(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="job_alerts"
    )

    role = models.CharField(
        max_length=200,
        help_text="Job role / keyword"
    )

    locations = models.CharField(
        max_length=300,
        help_text="Comma separated locations (e.g. Chennai,Bangalore)"
    )

    duration = models.CharField(
        max_length=50,
        help_text="Full-time / Internship / Part-time"
    )

    min_salary = models.IntegerField(null=True, blank=True)
    max_salary = models.IntegerField(null=True, blank=True)
    
    last_read_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    

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


class JobCategory(models.Model):
    name = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="jobs"
    )
    category = models.ForeignKey(
        JobCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jobs_category"
    )
    role = models.CharField(max_length=200)
    
    salary_min = models.IntegerField(help_text="Minimum salary in LPA",blank=True,null=True)
    salary_max = models.IntegerField(help_text="Maximum salary in LPA",blank=True,null=True)
    duration = models.CharField(
        max_length=50,
        help_text="Full-time / Internship / Contract"
    )
    posted_on = models.DateTimeField(auto_now_add=True)

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



class HelpIntent(models.Model):
    question = models.TextField()
    answer = models.TextField()
    keywords = models.CharField(
        max_length=500,
        help_text="Comma separated keywords"
    )

    def __str__(self):
        return self.question
    

class UnansweredQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return self.question





