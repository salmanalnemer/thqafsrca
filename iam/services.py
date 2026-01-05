from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Optional

from django.db.models import Q
from django.utils import timezone

from accounts.models import UserRole
from .models import AuditEvent, Permission, RolePermission, UserPermission

logger = logging.getLogger(__name__)

def get_client_ip(request) -> Optional[str]:
    try:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
    except Exception:
        return None

def audit(request, *, action: str, target_user=None, meta: Optional[dict[str, Any]] = None) -> None:
    try:
        AuditEvent.objects.create(
            actor=getattr(request, "user", None) if getattr(getattr(request, "user", None), "is_authenticated", False) else None,
            target_user=target_user,
            action=action,
            meta=meta or {},
            ip_address=get_client_ip(request),
            user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:4000],
        )
    except Exception:
        logger.exception("Failed to write audit event: %s", action)

@lru_cache(maxsize=50000)
def _cached_user_perm(user_id: int, perm_code: str) -> Optional[bool]:
    # Return True/False if explicitly set on user, else None
    row = (UserPermission.objects
           .filter(user_id=user_id, permission__code=perm_code, permission__is_active=True)
           .select_related("permission")
           .first())
    if row is None:
        return None
    return bool(row.allow)

@lru_cache(maxsize=50000)
def _cached_role_perm(role: str, perm_code: str) -> Optional[bool]:
    row = (RolePermission.objects
           .filter(role=role, permission__code=perm_code, permission__is_active=True)
           .select_related("permission")
           .first())
    if row is None:
        return None
    return bool(row.allow)

def user_has_perm(user, perm_code: str) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False

    # SUPER_ADMIN always allowed
    if getattr(user, "role", None) == UserRole.SUPER_ADMIN:
        return True

    # User override
    explicit = _cached_user_perm(int(user.id), perm_code)
    if explicit is not None:
        return explicit

    # Role default
    role = getattr(user, "role", "") or ""
    rp = _cached_role_perm(role, perm_code)
    if rp is not None:
        return rp

    return False

def invalidate_perm_cache() -> None:
    _cached_user_perm.cache_clear()
    _cached_role_perm.cache_clear()

def ensure_permission(code: str, name: str = "", module: str = "") -> Permission:
    perm, _ = Permission.objects.get_or_create(
        code=code,
        defaults={
            "name": name or code,
            "module": module or (code.split(".", 1)[0] if "." in code else ""),
        },
    )
    return perm
