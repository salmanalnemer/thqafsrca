from django.urls import path
from . import views

app_name = "staff"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("courses/open/", views.course_open, name="course_open"),
    path("courses/approve/", views.course_approve, name="course_approve"),
    path("courses/opened/", views.courses_opened, name="courses_opened"),
    path("courses/closed/", views.courses_closed, name="courses_closed"),
    path("courses/mine/", views.courses_mine, name="courses_mine"),
]
