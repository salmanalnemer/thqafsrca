from __future__ import annotations
from django.apps import AppConfig

class SysadminConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sysadmin"
    verbose_name = "لوحة مدير النظام"
