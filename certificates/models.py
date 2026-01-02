from __future__ import annotations

import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


class CertificateTemplate(models.Model):
    """
    قالب شهادة (اختياري الآن، مهم لاحقًا للطباعة والهوية)
    """
    name = models.CharField(max_length=120)
    region = models.ForeignKey("regions.Region", on_delete=models.SET_NULL, null=True, blank=True, related_name="certificate_templates")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Certificate(models.Model):
    """
    شهادة مرتبطة بتسجيل (Enrollment) — إصدار تلقائي بعد تأكيد الحضور.
    """
    enrollment = models.OneToOneField(
        "courses.Enrollment",
        on_delete=models.CASCADE,
        related_name="certificate",
    )

    template = models.ForeignKey(CertificateTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name="certificates")

    issued_at = models.DateTimeField(default=timezone.now)
    serial_number = models.CharField(max_length=40, unique=True, db_index=True)

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_certificates",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_serial() -> str:
        return secrets.token_urlsafe(16)

    def __str__(self):
        return f"Certificate {self.serial_number}"


class CertificateVerification(models.Model):
    """
    رمز تحقق عام (QR/Token) للتحقق من صحة الشهادة
    """
    certificate = models.OneToOneField(
        Certificate,
        on_delete=models.CASCADE,
        related_name="verification",
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    public_lookup_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(24)

    def __str__(self):
        return f"Verify {self.certificate.serial_number}"
