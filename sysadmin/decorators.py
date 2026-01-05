from __future__ import annotations

from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from accounts.models import UserRole


def sysadmin_required(view_func):
    """يسمح فقط لمدير النظام (super_admin)."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return redirect("accounts:login")

        if getattr(user, "role", None) != UserRole.SUPER_ADMIN:
            messages.error(request, "غير مصرح لك بالدخول إلى لوحة مدير النظام.")
            return redirect("home")

        return view_func(request, *args, **kwargs)
    return _wrapped
