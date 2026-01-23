from django.urls import path
from .views import NotificationListAPI, NotificationDetailAPI

urlpatterns = [
    path("notifications/", NotificationListAPI.as_view(), name="notification-list"),
    path("notifications/<int:id>/", NotificationDetailAPI.as_view(), name="notification-delete"),
    
]
