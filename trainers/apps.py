from django.apps import AppConfig

class TrainersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trainers"
    verbose_name = 'المدربين'

    def ready(self):
        from . import signals  # noqa
