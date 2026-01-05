# trainers/views.py
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from accounts.models import UserRole


def _deny_if_not_trainer(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("غير مصرح لك بالدخول.")
    if getattr(request.user, "role", None) != UserRole.TRAINER:
        try:
            messages.error(request, "غير مصرح لك بالدخول إلى لوحة المدربين.")
        except Exception:
            pass
        return HttpResponseForbidden("غير مصرح لك بالدخول.")
    return None


def _looks_like_email(s: str) -> bool:
    s = (s or "").strip()
    return ("@" in s) and (" " not in s)


def _safe_display_name(u, request) -> str:
    """
    ✅ يعرض الاسم الصحيح في الهيدر:
    1) الاسم الكامل من قاعدة البيانات (first_name/last_name) << أهم شيء
    2) display_name من السيشن إذا كان موجود (لكن نتجاهله إذا كان إيميل)
    3) حقول بديلة
    4) username
    5) آخر حل: جزء الإيميل قبل @
    """
    # 1) من قاعدة البيانات (الأولوية هنا عشان اسمك موجود بالفعل)
    try:
        full = (u.get_full_name() or "").strip()
        if full:
            return full
    except Exception:
        pass

    # أحيانًا يكون first_name/last_name موجودين لكن get_full_name ما رجّع
    first = (getattr(u, "first_name", "") or "").strip()
    last = (getattr(u, "last_name", "") or "").strip()
    if first or last:
        return f"{first} {last}".strip()

    # 2) من السيشن (لكن إذا كان إيميل نتجاهله)
    dn = (request.session.get("display_name") or "").strip()
    if dn and not _looks_like_email(dn) and dn != (getattr(u, "email", "") or "").strip():
        return dn

    # 3) حقول شائعة في موديلات مخصصة
    for attr in ("full_name", "name"):
        val = (getattr(u, attr, "") or "").strip()
        if val:
            return val

    # 4) username
    username = (getattr(u, "username", "") or "").strip()
    if username:
        return username

    # 5) آخر حل: local-part من الإيميل (بدون عرض الإيميل كامل)
    email = (getattr(u, "email", "") or "").strip()
    if email and "@" in email:
        return email.split("@", 1)[0]

    return "مستخدم"


def _safe_region_name(u) -> str:
    region = getattr(u, "region", None)
    if not region:
        return "—"

    name = (getattr(region, "name", "") or "").strip()
    if name:
        return name

    try:
        return str(region).strip() or "—"
    except Exception:
        return "—"


def _ctx(request, active: str):
    u = request.user
    return {
        "active": active,
        "display_name": _safe_display_name(u, request),
        "region_name": _safe_region_name(u),
    }


@login_required
def trainers_dashboard_view(request):
    denied = _deny_if_not_trainer(request)
    if denied:
        return denied
    return render(request, "trainers_temp/dashboard.html", _ctx(request, "dashboard"))


@login_required
def trainer_courses_view(request):
    denied = _deny_if_not_trainer(request)
    if denied:
        return denied
    return render(request, "trainers_temp/org_courses.html", _ctx(request, "courses"))


@login_required
def trainer_certificates_view(request):
    denied = _deny_if_not_trainer(request)
    if denied:
        return denied
    return render(request, "trainers_temp/org_certificates.html", _ctx(request, "certs"))
