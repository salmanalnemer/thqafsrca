from __future__ import annotations

from django.db import models


class Individual(models.Model):
    """
    ملف الفرد. قد يكون مستقل أو موظف جهة (OrgBranch).
    """
    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.PROTECT,
        related_name="individuals",
        null=True,
        blank=True,
    )
    org_branch = models.ForeignKey(
        "organizations.OrganizationBranch",
        on_delete=models.SET_NULL,
        related_name="individuals",
        null=True,
        blank=True,
    )

    full_name = models.CharField(max_length=200)
    national_id = models.CharField(max_length=30, blank=True, db_index=True)
    email = models.EmailField(db_index=True)  # للتوافق والبحث
    phone = models.CharField(max_length=20, blank=True)

    employee_id = models.CharField(max_length=50, blank=True, db_index=True)  # للموظفين
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["org_branch", "employee_id"]),
            models.Index(fields=["region"]),
        ]

    def __str__(self):
        return self.full_name
