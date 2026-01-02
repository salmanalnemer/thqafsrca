from __future__ import annotations

from django.db import models
from django.utils import timezone


class ConfirmationMethod(models.TextChoices):
    SELF_CONFIRM = "self_confirm", "تأكيد ذاتي"
    CODE = "code", "رمز حضور"
    QR = "qr", "QR"


class AttendanceConfirmation(models.Model):
    enrollment = models.OneToOneField(
        "courses.Enrollment",
        on_delete=models.CASCADE,
        related_name="attendance_confirmation",
        verbose_name="تسجيل الدورة",
    )

    method = models.CharField(
        max_length=20,
        choices=ConfirmationMethod.choices,
        default=ConfirmationMethod.SELF_CONFIRM,
        verbose_name="طريقة التأكيد",
    )
    confirmed_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ التأكيد")
    note = models.CharField(max_length=255, blank=True, verbose_name="ملاحظة")
    confirmation_code = models.CharField(max_length=50, blank=True, db_index=True, verbose_name="رمز التأكيد (اختياري)")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "تأكيد حضور"
        verbose_name_plural = "تأكيدات الحضور"

    def __str__(self):
        return f"تأكيد حضور لـ {self.enrollment}"
