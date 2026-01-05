from django.conf import settings
from django.db import models

class TrainerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trainer_profile",
        verbose_name="المستخدم",
    )
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "ملف مدرب"
        verbose_name_plural = "ملفات المدربين"

    def __str__(self) -> str:
        return self.user.get_full_name() or self.user.username

    @property
    def region(self):
        """
        ترجع منطقة المستخدم تلقائيًا
        (سواء فرد أو ممثل جهة)
        """
        return getattr(self.user, "region", None)
