from __future__ import annotations

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from accounts.models import User, UserRole
from iam.decorators import permission_required
from iam.models import AuditEvent, Permission, RolePermission, UserPermission, PermissionRequest
from iam.services import audit, invalidate_perm_cache

from .forms import UserUpdateForm, PermissionRequestDecisionForm

@permission_required("sysadmin.dashboard")
def dashboard(request):
    # quick stats
    stats = {
        "users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "pending_requests": PermissionRequest.objects.filter(status=PermissionRequest.Status.PENDING).count(),
        "audit_today": AuditEvent.objects.filter(created_at__date=timezone.now().date()).count(),
    }
    roles = User.objects.values("role").annotate(n=Count("id")).order_by("-n")
    return render(request, "sysadmin/dashboard.html", {"stats": stats, "roles": roles})

@permission_required("sysadmin.users")
def users_list(request):
    q = (request.GET.get("q") or "").strip()
    role = (request.GET.get("role") or "").strip()
    qs = User.objects.all().order_by("-date_joined")
    if q:
        qs = qs.filter(Q(email__icontains=q) | Q(full_name__icontains=q) | Q(phone__icontains=q))
    if role:
        qs = qs.filter(role=role)
    users = qs[:200]
    return render(request, "sysadmin/users_list.html", {"users": users, "q": q, "role": role, "roles": UserRole.choices})

@permission_required("sysadmin.user_edit")
@require_http_methods(["GET", "POST"])
def user_edit(request, user_id: int):
    u = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=u)
        if form.is_valid():
            before = {"role": u.role, "is_active": u.is_active, "region_id": u.region_id, "org_branch_id": u.org_branch_id, "individual_id": u.individual_id}
            form.save()
            after = {"role": u.role, "is_active": u.is_active, "region_id": u.region_id, "org_branch_id": u.org_branch_id, "individual_id": u.individual_id}
            invalidate_perm_cache()
            audit(request, action="user.update", target_user=u, meta={"before": before, "after": after})
            messages.success(request, "تم تحديث المستخدم.")
            return redirect("sysadmin:users")
        messages.error(request, "تحقق من الحقول.")
    else:
        form = UserUpdateForm(instance=u)
    # user overrides
    perms = Permission.objects.filter(is_active=True).order_by("module", "code")
    user_links = {up.permission_id: up for up in UserPermission.objects.filter(user=u)}
    return render(request, "sysadmin/user_edit.html", {"u": u, "form": form, "perms": perms, "user_links": user_links})

@permission_required("sysadmin.user_perm_toggle")
@require_POST
def user_perm_toggle(request, user_id: int, perm_id: int):
    u = get_object_or_404(User, id=user_id)
    p = get_object_or_404(Permission, id=perm_id)
    allow = (request.POST.get("allow") == "1")
    before = UserPermission.objects.filter(user=u, permission=p).first()
    with transaction.atomic():
        UserPermission.objects.update_or_create(user=u, permission=p, defaults={"allow": allow})
    invalidate_perm_cache()
    audit(request, action="userperm.set", target_user=u, meta={"permission": p.code, "allow": allow, "before": (before.allow if before else None)})
    messages.success(request, "تم تحديث صلاحية المستخدم.")
    return redirect("sysadmin:user_edit", user_id=u.id)

@permission_required("sysadmin.roles")
def roles_matrix(request):
    perms = Permission.objects.filter(is_active=True).order_by("module", "code")
    roles = [r[0] for r in UserRole.choices]
    links = RolePermission.objects.select_related("permission").all()
    matrix = {(l.role, l.permission_id): l.allow for l in links}
    return render(request, "sysadmin/roles_matrix.html", {"perms": perms, "roles": roles, "role_choices": UserRole.choices, "matrix": matrix})

@permission_required("sysadmin.role_perm_toggle")
@require_POST
def role_perm_toggle(request):
    role = request.POST.get("role") or ""
    perm_id = int(request.POST.get("perm_id") or "0")
    allow = (request.POST.get("allow") == "1")
    if role not in dict(UserRole.choices):
        messages.error(request, "Role غير صحيح.")
        return redirect("sysadmin:roles")
    p = get_object_or_404(Permission, id=perm_id)
    before = RolePermission.objects.filter(role=role, permission=p).first()
    with transaction.atomic():
        RolePermission.objects.update_or_create(role=role, permission=p, defaults={"allow": allow})
    invalidate_perm_cache()
    audit(request, action="roleperm.set", meta={"role": role, "permission": p.code, "allow": allow, "before": (before.allow if before else None)})
    messages.success(request, "تم تحديث صلاحية الدور.")
    return redirect("sysadmin:roles")

@permission_required("sysadmin.requests")
def requests_list(request):
    status = (request.GET.get("status") or "pending").strip()
    qs = PermissionRequest.objects.select_related("requested_by","target_user","permission").all()
    if status:
        qs = qs.filter(status=status)
    items = qs[:200]
    return render(request, "sysadmin/requests_list.html", {"items": items, "status": status, "Status": PermissionRequest.Status})

@permission_required("sysadmin.request_decide")
@require_http_methods(["GET", "POST"])
def request_decide(request, req_id: int):
    pr = get_object_or_404(PermissionRequest.objects.select_related("requested_by","target_user","permission"), id=req_id)
    if pr.status != PermissionRequest.Status.PENDING:
        messages.info(request, "تم اتخاذ قرار سابقًا.")
        return redirect("sysadmin:requests")
    if request.method == "POST":
        form = PermissionRequestDecisionForm(request.POST)
        if form.is_valid():
            decision = form.cleaned_data["decision"]
            note = form.cleaned_data["note"]
            with transaction.atomic():
                pr.decided_by = request.user
                pr.decided_at = timezone.now()
                if decision == "approve":
                    pr.status = PermissionRequest.Status.APPROVED
                    UserPermission.objects.update_or_create(
                        user=pr.target_user, permission=pr.permission, defaults={"allow": pr.allow}
                    )
                    invalidate_perm_cache()
                    audit(request, action="permrequest.approve", target_user=pr.target_user, meta={"permission": pr.permission.code, "allow": pr.allow, "note": note})
                    messages.success(request, "تم اعتماد الطلب وتطبيقه.")
                else:
                    pr.status = PermissionRequest.Status.REJECTED
                    audit(request, action="permrequest.reject", target_user=pr.target_user, meta={"permission": pr.permission.code, "allow": pr.allow, "note": note})
                    messages.success(request, "تم رفض الطلب.")
                pr.reason = (pr.reason + f"\n\n[قرار]: {note}").strip()
                pr.save()
            return redirect("sysadmin:requests")
        messages.error(request, "تحقق من المدخلات.")
    else:
        form = PermissionRequestDecisionForm()
    return render(request, "sysadmin/request_decide.html", {"pr": pr, "form": form})

@permission_required("sysadmin.audit")
def audit_log(request):
    q = (request.GET.get("q") or "").strip()
    qs = AuditEvent.objects.select_related("actor","target_user").all()
    if q:
        qs = qs.filter(Q(action__icontains=q) | Q(actor__email__icontains=q) | Q(target_user__email__icontains=q))
    items = qs[:200]
    return render(request, "sysadmin/audit.html", {"items": items, "q": q})
