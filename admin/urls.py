from django.urls import path

from . import views



urlpatterns = [
    path("overview/dashoard/",views.AdminOverviewDashboard.as_view(),name="admin_dashbboard")
]
