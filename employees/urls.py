
from django.urls import path
from .views import (
    EmployerForgotPasswordOTPAPI,
    ResetPasswordWithOTPAPI,
    EmployeeRegistrationAPI,
    JobCreateAPIView , JobCategoryCreateAPIView ,JobCategoryAPIView
)

urlpatterns = [

     path("register/", EmployeeRegistrationAPI.as_view(), name="employee-register"), #FOR SIGNUP PAGE 
     path("forgot-password/", EmployerForgotPasswordOTPAPI.as_view()),
    path("reset-password/", ResetPasswordWithOTPAPI.as_view()),
    path("jobs/create/",JobCreateAPIView.as_view(),name="job-create"),
    path( "job-categories/create/",JobCategoryCreateAPIView.as_view(), name="job-category-create"),
    path("job-categories/<int:pk>/",JobCategoryAPIView.as_view(),name="job-category-detail"),
    

]


