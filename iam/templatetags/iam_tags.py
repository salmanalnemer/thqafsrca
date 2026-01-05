from __future__ import annotations

from django import template
from iam.services import user_has_perm

register = template.Library()

@register.filter(name="has_perm")
def has_perm(user, code: str) -> bool:
    try:
        return user_has_perm(user, code)
    except Exception:
        return False
