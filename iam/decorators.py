from __future__ import annotations

from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse

from .services import user_has_perm

def permission_required(code: str):
    def deco(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('accounts:login')}?next={request.get_full_path()}")
            if not user_has_perm(request.user, code):
                return HttpResponseForbidden("غير مصرح لك.")
            return view_func(request, *args, **kwargs)
        _wrapped.required_permission = code  # for middleware discovery
        return _wrapped
    return deco
