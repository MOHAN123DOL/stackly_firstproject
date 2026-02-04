from django.urls import path
from .views import (JobSeekerAvatarAPI, JobSeekerRegistrationAPI , JobSeekerProfileAPI , 
                    ChangePasswordAPI, JobSeekerDashboardCountAPI ,LogoutAPI,CompanyJobsAPI , 
                    CompanyLogoUploadAPI , JobSeekerOpportunitiesCompanyListAPI ,  JobSeekerOpportunitiesOverviewAPI, LandingJobListingAPI)
urlpatterns = [
    path('jobseeker/avatar/', JobSeekerAvatarAPI.as_view(), name='jobseeker-avatar'),
    path('register/', JobSeekerRegistrationAPI.as_view(), name='jobseeker-register'),
    path("jobseeker/profile/", JobSeekerProfileAPI.as_view(), name="jobseeker-profile"),
    path("api/change-password/", ChangePasswordAPI.as_view(), name="change-password"),
    path("jobseeker/dashboard/counts/",JobSeekerDashboardCountAPI.as_view(),name="jobseeker-dashboard-counts"),
    path("api/logout/", LogoutAPI.as_view(), name="logout"),
    path("company/<int:company_id>/jobs/",CompanyJobsAPI.as_view(),name="company-jobs",),
    path("companies/<int:company_id>/upload-logo/",CompanyLogoUploadAPI.as_view(),name="company-logo-upload"),
    path("jobseeker/opportunities/companies/",JobSeekerOpportunitiesCompanyListAPI.as_view(),name="jobseeker-opportunities-companies"),
    path("opportunities/overview/",JobSeekerOpportunitiesOverviewAPI.as_view(),name="jobseeker-opportunities-overview"),
    path("landing/jobs/", LandingJobListingAPI.as_view(),name="jobseeker-landing-joblisting"),


     ]


