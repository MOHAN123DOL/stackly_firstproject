
from django.urls import path
from .views import EmployerForgotPasswordAPI
from .views import EmployeeRegistrationAPI
from jobseeker.views import JobSeekerRegistrationAPI

urlpatterns = [
    path(
        "forgot-password/",
        EmployerForgotPasswordAPI.as_view(),
        name="employer-forgot-password"
    ),
     path("register/", EmployeeRegistrationAPI.as_view(), name="employee-register"),
     

]



