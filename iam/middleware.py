from __future__ import annotations

from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.utils.deprecation import MiddlewareMixin

from .services import ensure_permission, user_has_perm

class IAMPermissionMiddleware(MiddlewareMixin):
    """
    Global permission enforcement:
    - Any authenticated request (except allowlist) must pass required permission.
    - Permission code is derived from namespace + url_name (e.g., courses.approve_list)
      and also the broader namespace.access (e.g., courses.access).
    """

    ALLOW_PREFIXES = (
        "/admin/",  # Django admin (you may restrict later)
        "/accounts/login",
        "/accounts/register",
        "/accounts/otp",
        "/accounts/logout",  # logout is handled via POST in your project
        "/static/",
        "/media/",
    )

    def process_view(self, request, view_func, view_args, view_kwargs):
        path = request.path or "/"\n        if path in {"/", "/favicon.ico"}:\n            return None
        for p in self.ALLOW_PREFIXES:
            if path.startswith(p):
                return None

        if not request.user.is_authenticated:
            return redirect(f"{reverse('accounts:login')}?next={request.get_full_path()}")        

        match = resolve(path)
        namespace = match.namespace or ""
        url_name = match.url_name or ""
        # fallback: first path segment
        if not namespace:
            seg = path.strip("/").split("/", 1)[0]
            namespace = seg or "core"

        # Broad access permission
        access_code = f"{namespace}.access"
        ensure_permission(access_code, name=f"دخول {namespace}", module=namespace)
        if not user_has_perm(request.user, access_code):
            return HttpResponseForbidden("غير مصرح لك بالدخول.")

        # Specific permission for endpoint if named
        if url_name:
            code = f"{namespace}.{url_name}"
            ensure_permission(code, name=code, module=namespace)
            if not user_has_perm(request.user, code):
                return HttpResponseForbidden("غير مصرح لك.")
        else:
            # If not named, enforce access only
            pass

        return None
