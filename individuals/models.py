from __future__ import annotations

from django.db import models


class Individual(models.Model):
    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.PROTECT,
        related_name="individuals",
        null=True,
        blank=True,
        verbose_name="المنطقة",
    )
    org_branch = models.ForeignKey(
        "organizations.OrganizationBranch",
        on_delete=models.SET_NULL,
        related_name="individuals",
        null=True,
        blank=True,
        verbose_name="فرع الجهة (اختياري)",
    )

    full_name = models.CharField(max_length=200, verbose_name="الاسم الكامل")
    national_id = models.CharField(max_length=30, blank=True, db_index=True, verbose_name="رقم الهوية (اختياري)")
    email = models.EmailField(db_index=True, verbose_name="البريد الإلكتروني")
    phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الجوال")

    employee_id = models.CharField(max_length=50, blank=True, db_index=True, verbose_name="الرقم الوظيفي (اختياري)")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "فرد"
        verbose_name_plural = "الأفراد"
        indexes = [
            models.Index(fields=["org_branch", "employee_id"]),
            models.Index(fields=["region"]),
        ]

    def __str__(self):
        return self.full_name
