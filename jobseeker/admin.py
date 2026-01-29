from django.contrib import admin
from .models import JobSeeker
from jobseeker.models import LandingChoice
@admin.register(JobSeeker)
class JobSeekerAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "first_name",
        "last_name",
        "created_at",
    )



@admin.register(LandingChoice)
class LandingChoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "role", "title", "is_active", "created_at")
    list_filter = ("is_active", "role")
    search_fields = ("title", "role")
    ordering = ("id",)
