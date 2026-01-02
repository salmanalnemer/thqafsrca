from __future__ import annotations

from django.db import models
from django.utils import timezone


class ConfirmationMethod(models.TextChoices):
    SELF_CONFIRM = "self_confirm", "تأكيد ذاتي"
    CODE = "code", "رمز حضور"
    QR = "qr", "QR"


class AttendanceConfirmation(models.Model):
    """
    حسب قراركم: بعد انتهاء الدورة، المستفيد يؤكد الحضور
    ثم تُصدر الشهادة تلقائيًا.
    """
    enrollment = models.OneToOneField(
        "courses.Enrollment",
        on_delete=models.CASCADE,
        related_name="attendance_confirmation",
    )

    method = models.CharField(max_length=20, choices=ConfirmationMethod.choices, default=ConfirmationMethod.SELF_CONFIRM)
    confirmed_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True)

    # لو قررتم لاحقًا إضافة رمز حضور/QR
    confirmation_code = models.CharField(max_length=50, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attendance for {self.enrollment}"
