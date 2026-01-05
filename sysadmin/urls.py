from __future__ import annotations
from django.urls import path
from . import views

app_name = "sysadmin"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.users_list, name="users"),
    path("users/<int:user_id>/", views.user_edit, name="user_edit"),
    path("users/<int:user_id>/perm/<int:perm_id>/", views.user_perm_toggle, name="user_perm_toggle"),
    path("roles/", views.roles_matrix, name="roles"),
    path("roles/toggle/", views.role_perm_toggle, name="role_perm_toggle"),
    path("requests/", views.requests_list, name="requests"),
    path("requests/<int:req_id>/", views.request_decide, name="request_decide"),
    path("audit/", views.audit_log, name="audit"),
]
