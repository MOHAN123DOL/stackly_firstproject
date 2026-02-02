from django.contrib import admin
from .models import JobSeeker
@admin.register(JobSeeker)
class JobSeekerAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "first_name",
        "last_name",
        "created_at",
    )


