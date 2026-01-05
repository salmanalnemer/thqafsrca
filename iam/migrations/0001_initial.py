from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0001_initial") if False else ("accounts", "0005_alter_user_role"),
    ]

    operations = [
        migrations.CreateModel(
            name="Permission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(db_index=True, max_length=190, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("module", models.CharField(blank=True, default="", max_length=64)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"verbose_name": "صلاحية", "verbose_name_plural": "الصلاحيات", "ordering": ["module", "code"]},
        ),
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(db_index=True, max_length=190)),
                ("meta", models.JSONField(blank=True, default=dict)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_actor", to=settings.AUTH_USER_MODEL)),
                ("target_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_target", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "سجل تدقيق", "verbose_name_plural": "سجل التدقيق", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="RolePermission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(db_index=True, max_length=32)),
                ("allow", models.BooleanField(default=True)),
                ("permission", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="role_links", to="iam.permission")),
            ],
            options={"verbose_name": "صلاحية دور", "verbose_name_plural": "صلاحيات الأدوار", "unique_together": {("role", "permission")}},
        ),
        migrations.CreateModel(
            name="UserPermission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("allow", models.BooleanField(default=True)),
                ("permission", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_links", to="iam.permission")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_perms", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "صلاحية مستخدم", "verbose_name_plural": "صلاحيات المستخدمين", "unique_together": {("user", "permission")}},
        ),
        migrations.CreateModel(
            name="PermissionRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("allow", models.BooleanField(default=True)),
                ("reason", models.TextField(blank=True, default="")),
                ("status", models.CharField(db_index=True, default="pending", max_length=16)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("decided_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="perm_requests_decided", to=settings.AUTH_USER_MODEL)),
                ("permission", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="iam.permission")),
                ("requested_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="perm_requests", to=settings.AUTH_USER_MODEL)),
                ("target_user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="perm_requests_target", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "طلب صلاحية", "verbose_name_plural": "طلبات الصلاحيات", "ordering": ["-created_at"]},
        ),
    ]
