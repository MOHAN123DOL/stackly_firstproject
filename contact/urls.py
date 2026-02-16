from django.urls import path
from .views import ContactMessageCreateAPIView

urlpatterns = [
    path("contact-us/", ContactMessageCreateAPIView.as_view(), name="contact-us"),
]