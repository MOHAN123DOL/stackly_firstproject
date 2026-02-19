from django.urls import path
from .views import (JobSeekerAvatarAPI, JobSeekerRegistrationAPI , JobSeekerProfileAPI , 
                    ChangePasswordAPI, JobSeekerDashboardCountAPI ,LogoutAPI,CompanyJobsAPI , 
                    CompanyLogoUploadAPI , JobSeekerOpportunitiesCompanyListAPI ,  JobSeekerOpportunitiesOverviewAPI,
                     LandingJobListingAPI,ApplyJobAPIView , JobAlertCreateAPIView , JobAlertListAPIView, 
                     JobAlertDetailAPIView, JobAlertMatchesAPIView,
                     JobAlertNewCountAPIView,JobCategoryListAPIView, 
                     JobCategoryAPI , ResumeUploadAPIView ,ProfileCompletionAPIView, SkillAssessmentAPIView,
                      JobseekerApplicationStatusAPIView , AIChatbotAPIView , JobseekerInterviewListAPIView)
urlpatterns = [
    path('jobseeker/avatar/', JobSeekerAvatarAPI.as_view(), name='jobseeker-avatar'),
    path('register/', JobSeekerRegistrationAPI.as_view(), name='jobseeker-register'),
    path("profile/", JobSeekerProfileAPI.as_view(), name="jobseeker-profile"),
    path("api/change-password/", ChangePasswordAPI.as_view(), name="change-password"),
    path("dashboard/counts/",JobSeekerDashboardCountAPI.as_view(),name="jobseeker-dashboard-counts"),
    path("api/logout/", LogoutAPI.as_view(), name="logout"),
    path("company/<int:company_id>/jobs/",CompanyJobsAPI.as_view(),name="company-jobs",),
    path("companies/<int:company_id>/upload-logo/",CompanyLogoUploadAPI.as_view(),name="company-logo-upload"),
    path("jobseeker/opportunities/companies/",JobSeekerOpportunitiesCompanyListAPI.as_view(),name="jobseeker-opportunities-companies"),
    path("opportunities/overview/",JobSeekerOpportunitiesOverviewAPI.as_view(),name="jobseeker-opportunities-overview"),
    path("landing/jobs/", LandingJobListingAPI.as_view(),name="jobseeker-landing-joblisting"),
    path("jobs/apply/", ApplyJobAPIView.as_view(), name="apply-job"),
    path("job-alerts/create/",JobAlertCreateAPIView.as_view(),name="job-alert-create"),
    path("job-alerts/", JobAlertListAPIView.as_view(), name="job-alert-list"),
    path("job-alerts/<int:pk>/",JobAlertDetailAPIView.as_view(),name="job-alert-detail"),
    path("job-alerts/<int:alert_id>/matches/",JobAlertMatchesAPIView.as_view(),name="job-alert-matches"),
    path("job-alerts/<int:alert_id>/new-count/",JobAlertNewCountAPIView.as_view(),name="job-alert-new-count"),
    path( "job-categories/list/",JobCategoryListAPIView.as_view(), name="job-category-lists"), 
    path("job-categories/list/<int:category_id>/",JobCategoryAPI.as_view(),name="job-category-jobs"),
    path("profile/resume/",ResumeUploadAPIView.as_view(),name="resume-upload"),
    path("profile/completion_details/",ProfileCompletionAPIView.as_view(),name="profile_completion_details"),
    path("profile/skill-assessment/", SkillAssessmentAPIView.as_view(),name="skills_assessment_score"),
     path("chatbot/help/", AIChatbotAPIView.as_view(),name="chat-bot"),
      path("interview/my/", JobseekerInterviewListAPIView.as_view(),name="interview_view"),
      path("applications/status/", JobseekerApplicationStatusAPIView.as_view(),name="application_view"),


     ]


