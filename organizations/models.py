from __future__ import annotations

from django.conf import settings
from django.db import models


class OrgStatus(models.TextChoices):
    PENDING = "pending", "بانتظار الاعتماد"
    APPROVED = "approved", "معتمد"
    REJECTED = "rejected", "مرفوض"
    SUSPENDED = "suspended", "موقوف"


class OrganizationMaster(models.Model):
    """
    الجهة الأم (مثال: وزارة الصحة)
    """
    name = models.CharField(max_length=200, unique=True)
    national_id = models.CharField(max_length=50, blank=True, db_index=True)  # اختياري
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class OrganizationBranch(models.Model):
    """
    فرع الجهة في منطقة محددة (مثال: وزارة الصحة - حائل)
    """
    master = models.ForeignKey(
        OrganizationMaster,
        on_delete=models.PROTECT,
        related_name="branches",
    )
    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.PROTECT,
        related_name="org_branches",
    )

    branch_name = models.CharField(max_length=200, blank=True)  # لو تحتاج اسم فرع داخلي
    address = models.CharField(max_length=300, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    status = models.CharField(
        max_length=20,
        choices=OrgStatus.choices,
        default=OrgStatus.PENDING,
        db_index=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_org_branches",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
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
    """
    ممثل الجهة (حساب مستخدم مرتبط بفرع معين)
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="org_representative",
    )
    org_branch = models.ForeignKey(
        OrganizationBranch,
        on_delete=models.CASCADE,
        related_name="representatives",
    )
    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["org_branch", "is_primary"])]

    def __str__(self):
        return f"{self.user.email} -> {self.org_branch}"
