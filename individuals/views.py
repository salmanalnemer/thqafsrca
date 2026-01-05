from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from accounts.models import UserRole


def _require_individual(request: HttpRequest) -> bool:
    """حارس صلاحيات بسيط للأفراد فقط."""
    if not request.user.is_authenticated:
        return False
    return getattr(request.user, "role", None) == UserRole.INDIVIDUAL


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    if not _require_individual(request):
        messages.error(request, "غير مصرح لك بالدخول إلى لوحة الأفراد.")
        return redirect("home")

    # NOTE:
    # هذا المشروع (الملف المضغوط) لا يحتوي على نماذج الدورات/الشهادات.
    # لذلك نعرضها كقوائم فارغة حاليًا، وعند إضافة apps (courses/certificates)
    # نربطها هنا مع فلترة صارمة حسب المستخدم والمنطقة.
    ctx = {
        "display_name": request.session.get("display_name") or (request.user.email.split("@")[0]),
        "region": getattr(getattr(request.user, "region", None), "name", ""),
        "courses": [],
        "certificates": [],
        "active": "dashboard",
    }
    return render(request, "individuals_temp/dashboard.html", ctx)


@login_required
def my_courses_view(request: HttpRequest) -> HttpResponse:
    if not _require_individual(request):
        messages.error(request, "غير مصرح لك بالدخول إلى دورات الأفراد.")
        return redirect("home")

    return render(
        request,
        "individuals_temp/my_courses.html",
        {
            "display_name": request.session.get("display_name") or (request.user.email.split("@")[0]),
            "region": getattr(getattr(request.user, "region", None), "name", ""),
            "courses": [],
            "active": "courses",
        },
    )


@login_required
def my_certificates_view(request: HttpRequest) -> HttpResponse:
    if not _require_individual(request):
        messages.error(request, "غير مصرح لك بالدخول إلى شهادات الأفراد.")
        return redirect("home")

    return render(
        request,
        "individuals_temp/my_certificates.html",
        {
            "display_name": request.session.get("display_name") or (request.user.email.split("@")[0]),
            "region": getattr(getattr(request.user, "region", None), "name", ""),
            "certificates": [],
            "active": "certs",
        },
    )
