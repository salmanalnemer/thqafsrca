from __future__ import annotations

from django.conf import settings
from django.db import models


class OrgStatus(models.TextChoices):
    PENDING = "pending", "بانتظار الاعتماد"
    APPROVED = "approved", "معتمد"
    REJECTED = "rejected", "مرفوض"
    SUSPENDED = "suspended", "موقوف"


class OrganizationMaster(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="اسم الجهة الأم")
    national_id = models.CharField(max_length=50, blank=True, db_index=True, verbose_name="رقم/معرف الجهة (اختياري)")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "جهة أم"
        verbose_name_plural = "الجهات الأم"

    def __str__(self):
        return self.name


class OrganizationBranch(models.Model):
    master = models.ForeignKey(
        OrganizationMaster,
        on_delete=models.PROTECT,
        related_name="branches",
        verbose_name="الجهة الأم",
    )
    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.PROTECT,
        related_name="org_branches",
        verbose_name="المنطقة",
    )

    branch_name = models.CharField(max_length=200, blank=True, verbose_name="اسم الفرع (اختياري)")
    address = models.CharField(max_length=300, blank=True, verbose_name="العنوان")
    phone = models.CharField(max_length=30, blank=True, verbose_name="هاتف الفرع")

    status = models.CharField(
        max_length=20,
        choices=OrgStatus.choices,
        default=OrgStatus.PENDING,
        db_index=True,
        verbose_name="حالة الاعتماد",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_org_branches",
        verbose_name="تم الاعتماد بواسطة",
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الاعتماد")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "فرع جهة"
        verbose_name_plural = "فروع الجهات"
        constraints = [
            models.UniqueConstraint(fields=["master", "region"], name="unique_master_region_branch")
        ]
        indexes = [
            models.Index(fields=["region", "status"]),
        ]

    def __str__(self):
        if self.branch_name:
            return f"{self.master.name} - {self.branch_name} ({self.region.name})"
        return f"{self.master.name} ({self.region.name})"


class OrganizationRepresentative(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="org_representative",
        verbose_name="حساب ممثل الجهة",
    )
    org_branch = models.ForeignKey(
        OrganizationBranch,
        on_delete=models.CASCADE,
        related_name="representatives",
        verbose_name="فرع الجهة",
    )
    is_primary = models.BooleanField(default=False, verbose_name="ممثل أساسي")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "ممثل جهة"
        verbose_name_plural = "ممثلو الجهات"
        indexes = [models.Index(fields=["org_branch", "is_primary"])]

    def __str__(self):
        return f"{self.user.email} -> {self.org_branch}"
