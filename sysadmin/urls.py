from django.urls import path
from . import views

app_name = "sysadmin"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.users_list, name="users_list"),
    path("users/<int:user_id>/", views.user_edit, name="user_edit"),
    path("audit/", views.audit_list, name="audit_list"),
]
