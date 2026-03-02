from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class JobSeeker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
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
    slug = models.SlugField(unique=True, blank=True) 
    location = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    company_logo = models.ImageField(
        upload_to="company_logos/",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True,blank=True)
    is_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

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

   
    skills_required = models.ManyToManyField(
        Skill,
        related_name="jobs",
        blank=True
    )


    min_experience = models.IntegerField(
        help_text="Minimum experience in years",
        null=True,
        blank=True
    )

    salary_min = models.IntegerField(blank=True, null=True)
    salary_max = models.IntegerField(blank=True, null=True)

    duration = models.CharField(
        max_length=50,
        help_text="Full-time / Internship / Contract"
    )

    posted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role} at {self.company.name}"


class UserAppliedJob(models.Model):

    STATUS_CHOICES = [
        ("APPLIED", "Applied"),
        ("UNDER_REVIEW", "Under Review"),
        ("SHORTLISTED", "Shortlisted"),
        ("REJECTED", "Rejected"),
        ("SELECTED", "Selected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True, related_name="applications")
    resume = models.FileField(upload_to="resumes/", null=True, blank=True,)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="APPLIED"
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "job")

    def __str__(self):
        return f"{self.user.username} - {self.job.role} - {self.status}"

    
class UserSavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True)
    is_anonymous = models.BooleanField(default=False)
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



class JobView(models.Model):
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="views"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("job", "user")

    def __str__(self):
        return f"{self.user.username} viewed {self.job.role}"

class JobseekerPreference(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="preferences"
    )

    preferred_skills = models.ManyToManyField(Skill, blank=True)

    preferred_location = models.CharField(max_length=150, blank=True)

    expected_salary_min = models.IntegerField(null=True, blank=True)
    expected_salary_max = models.IntegerField(null=True, blank=True)

    preferred_duration = models.CharField(
        max_length=50,
        blank=True
    )

    updated_at = models.DateTimeField(auto_now=True)


class JobseekerPrivacySettings(models.Model):
    PROFILE_VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("recruiters_only", "Recruiters Only"),
        ("private", "Private"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="privacy_settings"
    )

    profile_visibility = models.CharField(
        max_length=20,
        choices=PROFILE_VISIBILITY_CHOICES,
        default="recruiters_only"
    )

    show_email = models.BooleanField(default=False,help_text="NOTE :if you turn off employer not able to contact you")
    show_phone = models.BooleanField(default=False,help_text="NOTE :if you turn off employer not able to contact you")
    show_resume = models.BooleanField(default=True,help_text="NOTE :if you turn off employer not able to contact you")
    is_searchable = models.BooleanField(default=True,help_text="NOTE :if you turn off employer not able to search you")
    allow_anonymous_applications = models.BooleanField(default=False)
    allow_recruiter_messages = models.BooleanField(default=True,help_text="NOTE :if you turn off employer not able to message you")

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Privacy Settings"



class JobseekerActivityLog(models.Model):
    ACTION_CHOICES = [
        ("APPLIED_JOB", "Applied Job"),
        ("SAVED_JOB", "Saved Job"),
        ("VIEWED_JOB", "Viewed Job"),
        ("UPDATED_PROFILE", "Updated Profile"),
        ("UPLOADED_RESUME", "Uploaded Resume"),
        ("UPDATED_PREFERENCE", "Updated Preference"),
        ("UPDATED_PRIVACY", "Updated Privacy Settings"),
        ("UPDATED_AVATAR", "updated profile picture"),
        ("REMOVED_AVATAR","removed profile picture"),
        ("UPDATED_PASSWORD", "password changed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="activity_logs"
    )

    action_type = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.action_type}"
    

class JobRecommendationFeedback(models.Model):

    FEEDBACK_CHOICES = [
        ("LIKE", "Like"),
        ("DISLIKE", "Dislike"),
        ("NOT_RELEVANT", "Not Relevant"),
        ("HIDE", "Hide"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recommendation_feedbacks"
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="recommendation_feedbacks"
    )

    feedback_type = models.CharField(max_length=30, choices=FEEDBACK_CHOICES)
    rating = models.IntegerField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "job")





