# staff/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def _safe_full_name(user) -> str:
    """
    يرجّع الاسم الكامل (بدون أي fallback للإيميل).
    يحاول من:
    1) user.first_name + user.last_name
    2) user.get_full_name()
    3) user.profile (لو موجود) مثل full_name / first_name / last_name
    """
    # 1) حقول Django الافتراضية
    first = (getattr(user, "first_name", "") or "").strip()
    last  = (getattr(user, "last_name", "") or "").strip()
    if first and last:
        return f"{first} {last}".strip()
    if first:
        return first

    # 2) get_full_name
    try:
        gf = (user.get_full_name() or "").strip()
        if gf:
            return gf
    except Exception:
        pass

    # 3) profile (إذا عندك IndividualProfile / StaffProfile... الخ)
    prof = getattr(user, "profile", None)
    if prof is not None:
        full_name = (getattr(prof, "full_name", "") or "").strip()
        if full_name:
            return full_name

        pf = (getattr(prof, "first_name", "") or "").strip()
        pl = (getattr(prof, "last_name", "") or "").strip()
        if pf and pl:
            return f"{pf} {pl}".strip()
        if pf:
            return pf

    return ""


def _safe_region_from_user(user) -> str:
    reg = getattr(user, "region", None)
    if reg is not None:
        name = getattr(reg, "name", "") or getattr(reg, "title", "") or ""
        name = (name or "").strip()
        if name:
            return name

    prof = getattr(user, "profile", None)
    if prof is not None:
        name = getattr(prof, "region", "") or getattr(prof, "region_name", "") or ""
        name = (name or "").strip()
        if name:
            return name

    for attr in ("region_name", "region_title"):
        val = (getattr(user, attr, "") or "").strip()
        if val:
            return val

    return ""


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user

        role = getattr(user, "role", None)
        is_staff_user = bool(role)
        if not is_staff_user:
            messages.error(request, "غير مصرح لك بالدخول إلى لوحة المسؤولين.")
            return redirect("home")

        # ✅ ثبت مفاتيح السيشن (بدون لمس مفاتيح غير موجودة)
        request.session["display_name"] = _safe_full_name(user)  # ✅ الاسم الكامل فقط
        request.session["region"] = _safe_region_from_user(user)

        return view_func(request, *args, **kwargs)

    return _wrapped
