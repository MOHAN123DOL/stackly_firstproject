from django.contrib import admin
from .models import JobSeeker, ProjectPortfolio
@admin.register(JobSeeker)
class JobSeekerAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "first_name",
        "last_name",
        "created_at",
    )


@admin.register(ProjectPortfolio)
class ProjectPortfolioAdmin(admin.ModelAdmin):
    list_display = (
        "jobseeker",
        "title",
        "is_ongoing",
        "created_at",
    )


