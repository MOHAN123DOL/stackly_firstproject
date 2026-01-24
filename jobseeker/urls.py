from django.urls import path
from .views import (JobSeekerAvatarAPI, JobSeekerRegistrationAPI , JobSeekerProfileAPI , 
                    ChangePasswordAPI, JobSeekerDashboardCountAPI ,LogoutAPI)
urlpatterns = [
    path('jobseeker/avatar/', JobSeekerAvatarAPI.as_view(), name='jobseeker-avatar'),
    path('register/', JobSeekerRegistrationAPI.as_view(), name='jobseeker-register'),
    path("jobseeker/profile/", JobSeekerProfileAPI.as_view(), name="jobseeker-profile"),
     path("api/change-password/", ChangePasswordAPI.as_view(), name="change-password"),
     path("jobseeker/dashboard/counts/",JobSeekerDashboardCountAPI.as_view(),name="jobseeker-dashboard-counts"),
     path("api/logout/", LogoutAPI.as_view(), name="logout")

     ]


