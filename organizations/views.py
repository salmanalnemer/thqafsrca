# organizations/views.py
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from accounts.models import UserRole, OrganizationProfile


def _is_org_rep(user) -> bool:
    return getattr(user, "role", None) == UserRole.ORG_REP


def _deny_if_not_org(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("غير مصرح لك بالدخول.")
    if not _is_org_rep(request.user):
        return HttpResponseForbidden("غير مصرح لك بالدخول إلى لوحة الجهات.")
    return None


def _ctx(request, active: str):
    u = request.user

    # اسم العرض من السيشن (الذي أنت تحفظه بعد login)
    display_name = (request.session.get("display_name") or "").strip()
    if not display_name:
        display_name = getattr(u, "email", "") or "مستخدم"

    # اسم الجهة من OrganizationProfile
    org_name = ""
    try:
        org = OrganizationProfile.objects.filter(user=u).only("organization_name").first()
        if org and (org.organization_name or "").strip():
            org_name = org.organization_name.strip()
    except Exception:
        org_name = ""

    return {
        "active": active,
        "display_name": display_name,
        "region": getattr(u, "region", None),
        "org_name": org_name,
    }


@login_required
def dashboard_view(request):
    denied = _deny_if_not_org(request)
    if denied:
        return denied
    return render(request, "organizations_temp/dashboard.html", _ctx(request, "dashboard"))


@login_required
def org_courses_view(request):
    denied = _deny_if_not_org(request)
    if denied:
        return denied
    return render(request, "organizations_temp/org_courses.html", _ctx(request, "courses"))


@login_required
def org_certificates_view(request):
    denied = _deny_if_not_org(request)
    if denied:
        return denied
    return render(request, "organizations_temp/org_certificates.html", _ctx(request, "certs"))
