from __future__ import annotations

from django.apps import AppConfig

class IamConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "iam"
    verbose_name = "IAM / الصلاحيات"

    def ready(self) -> None:
        # Register signals
        from . import signals  # noqa
