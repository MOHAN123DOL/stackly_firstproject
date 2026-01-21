from django.urls import path
from .views import JobSeekerAvatarAPI, JobSeekerRegistrationAPI , JobSeekerProfileAPI , ChangePasswordAPI
urlpatterns = [
    path('jobseeker/avatar/', JobSeekerAvatarAPI.as_view(), name='jobseeker-avatar'),
    path('register/', JobSeekerRegistrationAPI.as_view(), name='jobseeker-register'),
    path("jobseeker/profile/", JobSeekerProfileAPI.as_view(), name="jobseeker-profile"),
     path("api/change-password/", ChangePasswordAPI.as_view(), name="change-password"),
]




