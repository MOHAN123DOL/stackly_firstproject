
from django.urls import path
from .views import EmployeeRegistrationAPI 
from .views import (
    EmployerForgotPasswordOTPAPI,
    ResetPasswordWithOTPAPI
)

urlpatterns = [

     path("register/", EmployeeRegistrationAPI.as_view(), name="employee-register"), #FOR SIGNUP PAGE 
     path("forgot-password/", EmployerForgotPasswordOTPAPI.as_view()),
    path("reset-password/", ResetPasswordWithOTPAPI.as_view()),
     

]



urlpatterns = [
    path("forgot-password/", EmployerForgotPasswordOTPAPI.as_view()),
    path("reset-password/", ResetPasswordWithOTPAPI.as_view()),
]

