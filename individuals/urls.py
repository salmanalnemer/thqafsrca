from django.urls import path

from . import views


app_name = "individuals"


urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("courses/", views.my_courses_view, name="my_courses"),
    path("certificates/", views.my_certificates_view, name="my_certificates"),
]
