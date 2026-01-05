from django.urls import path
from . import views

app_name = "trainers"

urlpatterns = [
    path("dashboard/", views.trainers_dashboard_view, name="dashboard"),
    path("courses/", views.trainer_courses_view, name="trainer_courses"),
    path("certificates/", views.trainer_certificates_view, name="trainer_certificates"),
]
