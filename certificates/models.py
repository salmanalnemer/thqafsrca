from __future__ import annotations

import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


class CertificateTemplate(models.Model):
    name = models.CharField(max_length=120, verbose_name="اسم القالب")
    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificate_templates",
        verbose_name="المنطقة (اختياري)",
    )
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "قالب شهادة"
        verbose_name_plural = "قوالب الشهادات"

    def __str__(self):
        return self.name


class Certificate(models.Model):
    enrollment = models.OneToOneField(
        "courses.Enrollment",
        on_delete=models.CASCADE,
        related_name="certificate",
        verbose_name="تسجيل الدورة",
    )

    template = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates",
        verbose_name="القالب (اختياري)",
    )

    issued_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الإصدار")
    serial_number = models.CharField(max_length=40, unique=True, db_index=True, verbose_name="رقم تسلسلي")

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_certificates",
        verbose_name="أُصدرت بواسطة (اختياري)",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "شهادة"
        verbose_name_plural = "الشهادات"

    @staticmethod
    def generate_serial() -> str:
        return secrets.token_urlsafe(16)

    def __str__(self):
        return f"شهادة {self.serial_number}"


class CertificateVerification(models.Model):
    certificate = models.OneToOneField(
        Certificate,
        on_delete=models.CASCADE,
        related_name="verification",
        verbose_name="الشهادة",
    )
    token = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="رمز التحقق")
    public_lookup_enabled = models.BooleanField(default=True, verbose_name="إتاحة التحقق العام")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "تحقق شهادة"
        verbose_name_plural = "التحقق من الشهادات"

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(24)

    def __str__(self):
        return f"تحقق لـ {self.certificate.serial_number}"
