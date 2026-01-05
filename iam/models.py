from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.models import UserRole

class Permission(models.Model):
    code = models.CharField(max_length=190, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    module = models.CharField(max_length=64, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "صلاحية"
        verbose_name_plural = "الصلاحيات"
        ordering = ["module", "code"]

    def __str__(self) -> str:
        return self.code


class RolePermission(models.Model):
    role = models.CharField(max_length=32, choices=UserRole.choices, db_index=True)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="role_links")
    allow = models.BooleanField(default=True)

    class Meta:
        verbose_name = "صلاحية دور"
        verbose_name_plural = "صلاحيات الأدوار"
        unique_together = [("role", "permission")]
        indexes = [
            models.Index(fields=["role", "permission"]),
        ]

    def __str__(self) -> str:
        return f"{self.role} -> {self.permission.code} ({'allow' if self.allow else 'deny'})"


class UserPermission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_perms")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="user_links")
    allow = models.BooleanField(default=True)

    class Meta:
        verbose_name = "صلاحية مستخدم"
        verbose_name_plural = "صلاحيات المستخدمين"
        unique_together = [("user", "permission")]
        indexes = [
            models.Index(fields=["user", "permission"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} -> {self.permission.code} ({'allow' if self.allow else 'deny'})"


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_actor")
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_target")
    action = models.CharField(max_length=190, db_index=True)
    meta = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "سجل تدقيق"
        verbose_name_plural = "سجل التدقيق"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.action}"


class PermissionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "قيد المراجعة"
        APPROVED = "approved", "مقبول"
        REJECTED = "rejected", "مرفوض"

    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perm_requests")
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perm_requests_target")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    allow = models.BooleanField(default=True)
    reason = models.TextField(blank=True, default="")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="perm_requests_decided")
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "طلب صلاحية"
        verbose_name_plural = "طلبات الصلاحيات"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.permission.code} for {self.target_user_id} ({self.get_status_display()})"
