from django.urls import path
from .views import LandingChoiceAPI , LandingInfoCardAPI 

urlpatterns = [
     path("choices/",LandingChoiceAPI.as_view(),name="landing-choices"),
     path("infocards/", LandingInfoCardAPI.as_view(), name="landing-infocards"),
     
     
      ]