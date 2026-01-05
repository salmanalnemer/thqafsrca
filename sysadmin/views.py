from __future__ import annotations

import logging
from typing import Any

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User, UserRole
from organizations.models import OrganizationBranch
from regions.models import Region

from .decorators import sysadmin_required
from .models import AuditLog

logger = logging.getLogger(__name__)


def _client_ip(request: HttpRequest) -> str | None:
    # خلف Proxy استخدم X-Forwarded-For إن كان مضبوط عندكم
    xff = (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
    if xff:
        return xff
    return (request.META.get("REMOTE_ADDR") or None)


def _ua(request: HttpRequest) -> str:
    return (request.META.get("HTTP_USER_AGENT") or "")[:256]


def _snapshot_user(u: User) -> dict[str, Any]:
    return {
        "id": u.id,
        "email": u.email,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "phone": getattr(u, "phone", ""),
        "role": u.role,
        "is_active": u.is_active,
        "region_id": u.region_id,
        "org_branch_id": u.org_branch_id,
    }


def _audit(request: HttpRequest, action: str, target: User | None, before: dict | None, after: dict | None, note: str = "") -> None:
    try:
        AuditLog.objects.create(
            actor=request.user if request.user.is_authenticated else None,
            action=action,
            target_user=target,
            ip_address=_client_ip(request),
            user_agent=_ua(request),
            before=before,
            after=after,
            note=(note or "")[:250],
        )
    except Exception:
        logger.exception("Failed to write AuditLog")


class UserFilterForm(forms.Form):
    q = forms.CharField(required=False, label="بحث")
    role = forms.ChoiceField(
        required=False,
        label="الدور",
        choices=[("", "الكل")] + list(UserRole.choices),
    )
    region = forms.ModelChoiceField(
        required=False,
        label="المنطقة",
        queryset=Region.objects.all().order_by("name"),
        empty_label="الكل",
    )


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "role", "is_active", "region", "org_branch"]
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "off"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "off"}),
            "phone": forms.TextInput(attrs={"autocomplete": "off", "dir": "ltr"}),
        }

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        region = cleaned.get("region")
        org_branch = cleaned.get("org_branch")

        # قواعد نطاق بسيطة (مبدئية)
        if role in {UserRole.REGION_MANAGER, UserRole.SUPERVISOR, UserRole.COORDINATOR, UserRole.TRAINER} and not region:
            raise forms.ValidationError("هذا الدور يتطلب تحديد المنطقة.")
        if role == UserRole.ORG_REP and not org_branch:
            raise forms.ValidationError("ممثل الجهة يتطلب تحديد فرع الجهة.")
        return cleaned


@login_required
@sysadmin_required
def dashboard(request: HttpRequest) -> HttpResponse:
    ctx = {
        "active": "dashboard",
        "stats": {
            "users_total": User.objects.count(),
            "users_active": User.objects.filter(is_active=True).count(),
            "org_reps": User.objects.filter(role=UserRole.ORG_REP).count(),
            "trainers": User.objects.filter(role=UserRole.TRAINER).count(),
        },
        "recent_audit": AuditLog.objects.select_related("actor", "target_user")[:8],
    }
    return render(request, "sysadmin_temp/dashboard.html", ctx)


@login_required
@sysadmin_required
def users_list(request: HttpRequest) -> HttpResponse:
    form = UserFilterForm(request.GET or None)
    qs = User.objects.select_related("region", "org_branch").order_by("-date_joined")

    if form.is_valid():
        q = (form.cleaned_data.get("q") or "").strip()
        role = form.cleaned_data.get("role") or ""
        region = form.cleaned_data.get("region")

        if q:
            qs = qs.filter(email__icontains=q) | qs.filter(first_name__icontains=q) | qs.filter(last_name__icontains=q)
        if role:
            qs = qs.filter(role=role)
        if region:
            qs = qs.filter(region=region)

    ctx = {
        "active": "users",
        "form": form,
        "users": qs[:200],  # سقف حماية للأداء
    }
    return render(request, "sysadmin_temp/users_list.html", ctx)


@login_required
@sysadmin_required
def user_edit(request: HttpRequest, user_id: int) -> HttpResponse:
    u = get_object_or_404(User.objects.select_related("region", "org_branch"), pk=user_id)
    before = _snapshot_user(u)

    if request.method == "POST":
        form = UserEditForm(request.POST, instance=u)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            after = _snapshot_user(u)

            # تحديد نوع التدقيق
            action = "user_update"
            if before.get("role") != after.get("role"):
                action = "role_change"
            elif before.get("region_id") != after.get("region_id") or before.get("org_branch_id") != after.get("org_branch_id"):
                action = "scope_change"
            elif before.get("is_active") != after.get("is_active"):
                action = "user_enable" if after.get("is_active") else "user_disable"

            _audit(request, action=action, target=u, before=before, after=after, note="تعديل عبر لوحة مدير النظام")
            messages.success(request, "تم حفظ التغييرات بنجاح.")
            return redirect("sysadmin:users_list")
        else:
            messages.error(request, "تأكد من الحقول وحاول مرة أخرى.")
    else:
        form = UserEditForm(instance=u)

    ctx = {
        "active": "users",
        "u": u,
        "form": form,
        "regions": Region.objects.all().order_by("name"),
        "branches": OrganizationBranch.objects.select_related("organization").all().order_by("organization__name", "name"),
    }
    return render(request, "sysadmin_temp/user_edit.html", ctx)


@login_required
@sysadmin_required
def audit_list(request: HttpRequest) -> HttpResponse:
    logs = AuditLog.objects.select_related("actor", "target_user")[:250]
    return render(request, "sysadmin_temp/audit_list.html", {"active": "audit", "logs": logs})
