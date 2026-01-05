from __future__ import annotations

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """سجل تدقيق لتغييرات لوحة مدير النظام."""
    ACTION_CHOICES = [
        ("user_create", "إنشاء مستخدم"),
        ("user_update", "تحديث مستخدم"),
        ("user_disable", "تعطيل مستخدم"),
        ("user_enable", "تفعيل مستخدم"),
        ("role_change", "تغيير دور"),
        ("scope_change", "تغيير نطاق (منطقة/جهة)"),
        ("password_reset", "إعادة تعيين كلمة مرور"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_actor_logs",
        verbose_name="المنفذ",
    )
    action = models.CharField(max_length=32, choices=ACTION_CHOICES, db_index=True, verbose_name="الإجراء")
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_target_logs",
        verbose_name="المستخدم المستهدف",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="عنوان IP")
    user_agent = models.CharField(max_length=256, blank=True, default="", verbose_name="User-Agent")

    # Snapshot مبسط (قبل/بعد)
    before = models.JSONField(null=True, blank=True, verbose_name="قبل")
    after = models.JSONField(null=True, blank=True, verbose_name="بعد")

    note = models.CharField(max_length=250, blank=True, default="", verbose_name="ملاحظة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "سجل تدقيق"
        verbose_name_plural = "سجلات التدقيق"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} @ {self.created_at:%Y-%m-%d %H:%M}"
