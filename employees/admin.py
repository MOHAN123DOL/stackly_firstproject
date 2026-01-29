
from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "company_name", "designation", "created_at")
    search_fields = ("company_name", "user__username")
