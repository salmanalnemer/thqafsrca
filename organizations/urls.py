from django.urls import path
from . import views

app_name = "organizations"

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("courses/", views.org_courses_view, name="org_courses"),
    path("certificates/", views.org_certificates_view, name="org_certificates"),
]
