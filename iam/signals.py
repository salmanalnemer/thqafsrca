from __future__ import annotations

import logging
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.urls import get_resolver, URLPattern, URLResolver

from .services import ensure_permission

logger = logging.getLogger(__name__)

def _walk(urlpatterns, namespace_prefix=""):
    for p in urlpatterns:
        if isinstance(p, URLResolver):
            ns = p.namespace or ""
            new_prefix = ns or namespace_prefix
            yield from _walk(p.url_patterns, new_prefix)
        elif isinstance(p, URLPattern):
            name = p.name or ""
            yield namespace_prefix, name

@receiver(post_migrate)
def sync_permissions(sender, **kwargs):
    # Only run once for our app installs, but safe to run multiple times.
    try:
        resolver = get_resolver()
        namespaces=set()
        for ns, name in _walk(resolver.url_patterns, ""):
            if ns:
                namespaces.add(ns)
                ensure_permission(f"{ns}.access", name=f"دخول {ns}", module=ns)
                if name:
                    ensure_permission(f"{ns}.{name}", name=f"{ns}.{name}", module=ns)
        # Core access (home)
        ensure_permission("core.access", name="دخول الموقع", module="core")
        ensure_permission("core.home", name="الصفحة الرئيسية", module="core")
    except Exception:
        logger.exception("sync_permissions failed")


from accounts.models import UserRole
from .models import RolePermission, Permission

def _seed_role_permissions():
    if RolePermission.objects.exists():
        return
    # Ensure some baseline permissions per role (you can adjust from SysAdmin UI)
    baseline = {
        UserRole.REGION_MANAGER: ["core.access", "regions.access", "staff.access", "support.access"],
        UserRole.SUPERVISOR: ["core.access", "staff.access", "support.access"],
        UserRole.COORDINATOR: ["core.access", "courses.access", "attendance.access", "certificates.access", "support.access"],
        UserRole.TRAINER: ["core.access", "trainers.access", "courses.access", "certificates.access"],
        UserRole.ORG_REP: ["core.access", "organizations.access", "courses.access"],
        UserRole.INDIVIDUAL: ["core.access", "individuals.access", "courses.access", "certificates.access"],
    }
    for role, codes in baseline.items():
        for code in codes:
            perm = Permission.objects.filter(code=code).first()
            if not perm:
                perm = ensure_permission(code, name=code, module=code.split('.',1)[0])
            RolePermission.objects.get_or_create(role=role, permission=perm, defaults={"allow": True})

@receiver(post_migrate)
def seed_role_permissions(sender, **kwargs):
    try:
        _seed_role_permissions()
    except Exception:
        logger.exception("seed_role_permissions failed")
