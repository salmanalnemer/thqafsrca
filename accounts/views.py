# accounts/views.py
from __future__ import annotations

import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from .models import EmailOTP, IndividualProfile, OrganizationProfile, User, UserRole

logger = logging.getLogger(__name__)

SA_NATIONAL_ID_RE = re.compile(r"^\d{10}$")
PHONE_RE = re.compile(r"^\+?\d{8,15}$")

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 6
OTP_RESEND_COOLDOWN_SECONDS = 60

# ✅ أدوار لوحة المسؤولين (عدّلها حسب مسمياتك الفعلية في UserRole)
STAFF_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.REGION_MANAGER,
    UserRole.SUPERVISOR,
    UserRole.COORDINATOR,
}

# ✅ الأدوار المسموح لها باستخدام بوابة الدخول العامة (نفس الهوم)
ALLOWED_PORTAL_ROLES = {
    UserRole.INDIVIDUAL,
    UserRole.ORG_REP,
    *STAFF_ROLES,
}


# -----------------------------
# Helpers
# -----------------------------
def _safe_decimal(value: str) -> Decimal | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def _clean_and_validate_email(raw: str) -> str:
    """
    Normalize and validate an email address (ASCII-only) before using it in SMTP.
    """
    email = (raw or "").strip()
    if not email:
        raise ValueError("Email is empty.")

    try:
        email.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("Invalid email address (non-ASCII characters).") from exc

    try:
        validate_email(email)
    except ValidationError as exc:
        raise ValueError("Invalid email address format.") from exc

    return email.lower()


def os_getenv(k: str) -> str:
    try:
        import os
        return (os.getenv(k, "") or "").strip()
    except Exception:
        return ""


def _no_reply_email() -> str:
    return (
        (getattr(settings, "THQAF_NO_REPLY_EMAIL", "") or "").strip()
        or os_getenv("THQAF_NO_REPLY_EMAIL")
        or "no-reply@thqaf.com"
    )


def _support_email() -> str:
    return (
        (getattr(settings, "THQAF_SUPPORT_EMAIL", "") or "").strip()
        or os_getenv("THQAF_SUPPORT_EMAIL")
        or "support@thqaf.com"
    )


def _logo_url_default() -> str:
    return (getattr(settings, "THQAF_LOGO_URL", "") or "").strip() or os_getenv("THQAF_LOGO_URL") or ""


def _send_html_email(
    *,
    to_email: str,
    subject: str,
    txt_template: str,
    html_template: str | None,
    ctx: dict,
    from_email: str,
    reply_to: str | None = None,
) -> None:
    """
    إرسال رسالة HTML + TXT بشكل آمن (مع تحقق بريد المستلم).
    """
    to_email = _clean_and_validate_email(to_email)
    text_body = render_to_string(txt_template, ctx)

    html_body = None
    if html_template:
        try:
            html_body = render_to_string(html_template, ctx)
        except Exception:
            html_body = None

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=[to_email],
        reply_to=[reply_to] if reply_to else None,
    )

    if html_body:
        msg.attach_alternative(html_body, "text/html")

    sent = msg.send(fail_silently=False)
    if sent != 1:
        raise RuntimeError(f"Email backend returned sent_count={sent}")


# -----------------------------
# Redirect by role (✅ من نفس الهوم)
# -----------------------------
def _redirect_by_role(request, user: User):
    """
    ✅ نفس صفحة الدخول للجميع، وبعد التحقق يتم التوجيه حسب الدور.
    ملاحظة: يتطلب وجود staff app بمسار name='staff:dashboard'
    """
    role = getattr(user, "role", None)

    if role in STAFF_ROLES:
        return _safe_next(request, "staff:dashboard")

    if role == UserRole.INDIVIDUAL:
        return _safe_next(request, "individuals:dashboard")

    if role == UserRole.ORG_REP:
        return _safe_next(request, "organizations:dashboard")

    # أي دور غير معروف/غير مسموح
    try:
        logout(request)
    except Exception:
        pass
    messages.error(request, "غير مصرح لك بالدخول.")
    return redirect("accounts:login")


# -----------------------------
# Emails (verification / login otp / course notification / contact)
# -----------------------------
def _send_verify_email_otp(email: str, code: str) -> None:
    subject = "تفعيل حسابك في منصة ثقف"
    ctx = {
        "otp_code": code,
        "ttl_minutes": OTP_TTL_MINUTES,
        "year": timezone.now().year,
        "user_name": "بك",
        "logo_url": _logo_url_default(),
        "support_email": _support_email(),
    }

    _send_html_email(
        to_email=email,
        subject=subject,
        txt_template="emails/verify_email.txt",
        html_template="emails/verify_email.html",
        ctx=ctx,
        from_email=_no_reply_email(),
        reply_to=_support_email(),
    )


def _send_login_otp_email(email: str, code: str) -> None:
    subject = "رمز التحقق لتسجيل الدخول - ثقف"
    ctx = {
        "otp_code": code,
        "ttl_minutes": OTP_TTL_MINUTES,
        "year": timezone.now().year,
        "user_name": "بك",
        "logo_url": _logo_url_default(),
        "support_email": _support_email(),
    }

    _send_html_email(
        to_email=email,
        subject=subject,
        txt_template="emails/login_otp.txt",
        html_template="emails/login_otp.html",
        ctx=ctx,
        from_email=_no_reply_email(),
        reply_to=_support_email(),
    )


def send_course_notification_email(
    *,
    to_email: str,
    course_title: str,
    start_at: str | None = None,
    extra: str | None = None,
) -> None:
    subject = f"إشعار دورة تدريبية: {course_title}"
    ctx = {
        "course_title": course_title,
        "start_at": start_at,
        "extra": extra,
        "year": timezone.now().year,
        "logo_url": _logo_url_default(),
        "support_email": _support_email(),
    }

    _send_html_email(
        to_email=to_email,
        subject=subject,
        txt_template="emails/course_notification.txt",
        html_template="emails/course_notification.html",
        ctx=ctx,
        from_email=_no_reply_email(),
        reply_to=_support_email(),
    )


def send_contact_us_email(*, from_name: str, from_email: str, message_text: str) -> None:
    from_email_clean = _clean_and_validate_email(from_email)

    subject = f"رسالة تواصل معنا - {from_name}"
    to_support = _support_email()

    ctx = {
        "from_name": from_name,
        "from_email": from_email_clean,
        "message_text": message_text,
        "year": timezone.now().year,
        "logo_url": _logo_url_default(),
        "support_email": to_support,
    }

    _send_html_email(
        to_email=to_support,
        subject=subject,
        txt_template="emails/contact_us.txt",
        html_template="emails/contact_us.html",
        ctx=ctx,
        from_email=_no_reply_email(),
        reply_to=from_email_clean,
    )


# -----------------------------
# Rate limits
# -----------------------------
def _rate_limit_resend_ok(request) -> bool:
    last = request.session.get("otp_last_sent_at")
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last)
        if timezone.is_naive(last_dt):
            last_dt = timezone.make_aware(last_dt, timezone.get_current_timezone())
        delta = (timezone.now() - last_dt).total_seconds()
        return delta >= OTP_RESEND_COOLDOWN_SECONDS
    except Exception:
        return True


def _mark_otp_sent_now(request) -> None:
    request.session["otp_last_sent_at"] = timezone.now().isoformat()


def _rate_limit_resend_ok_login(request) -> bool:
    last = request.session.get("otp_login_last_sent_at")
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last)
        if timezone.is_naive(last_dt):
            last_dt = timezone.make_aware(last_dt, timezone.get_current_timezone())
        delta = (timezone.now() - last_dt).total_seconds()
        return delta >= OTP_RESEND_COOLDOWN_SECONDS
    except Exception:
        return True


def _mark_otp_login_sent_now(request) -> None:
    request.session["otp_login_last_sent_at"] = timezone.now().isoformat()


def _get_regions_and_org_branches():
    regions = []
    org_branches = []

    try:
        from regions.models import Region  # type: ignore
        regions = Region.objects.all().order_by("id")
    except Exception as e:
        logger.warning("Could not load regions: %s", e)

    try:
        from organizations.models import OrganizationBranch  # type: ignore
        org_branches = OrganizationBranch.objects.all().order_by("id")
    except Exception as e:
        logger.warning("Could not load organization branches: %s", e)

    return regions, org_branches


def _validate_region_id(region_id: str) -> int | None:
    region_id = (region_id or "").strip()
    if not region_id:
        return None
    try:
        rid = int(region_id)
        if rid <= 0:
            return None
        return rid
    except Exception:
        return None


def _get_display_name(user: User) -> str:
    try:
        if user.role == UserRole.INDIVIDUAL:
            prof = IndividualProfile.objects.filter(user=user).only("full_name").first()
            if prof and (prof.full_name or "").strip():
                return prof.full_name.strip()

        if user.role == UserRole.ORG_REP:
            org = OrganizationProfile.objects.filter(user=user).only(
                "representative_name", "organization_name"
            ).first()
            if org:
                if (org.representative_name or "").strip():
                    return org.representative_name.strip()
                if (org.organization_name or "").strip():
                    return org.organization_name.strip()
    except Exception:
        pass

    email = (getattr(user, "email", "") or "").strip()
    if "@" in email:
        return email.split("@", 1)[0]
    return "مستخدم"


def _safe_next(request, fallback_url_name: str):
    nxt = (request.POST.get("next") or request.GET.get("next") or "").strip()
    if nxt and url_has_allowed_host_and_scheme(
        nxt,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(nxt)
    return redirect(fallback_url_name)


# -----------------------------
# Register
# -----------------------------
@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == "GET":
        regions, org_branches = _get_regions_and_org_branches()
        return render(request, "accounts_temp/register.html", {"regions": regions, "org_branches": org_branches})

    account_type = (request.POST.get("account_type") or "").strip()  # individual | org
    email = (request.POST.get("email") or "").strip().lower()
    phone = (request.POST.get("phone") or "").strip()
    password = (request.POST.get("password") or "").strip()
    confirm_password = (request.POST.get("confirm_password") or "").strip()

    if account_type not in ("individual", "org"):
        messages.error(request, "نوع التسجيل غير صحيح.")
        return redirect("accounts:register")

    if not email or not phone or not password or not confirm_password:
        messages.error(request, "فضلاً أكمل جميع الحقول المطلوبة.")
        return redirect("accounts:register")

    if password != confirm_password:
        messages.error(request, "كلمتا المرور غير متطابقتين.")
        return redirect("accounts:register")

    if not PHONE_RE.match(phone):
        messages.error(request, "رقم الجوال غير صحيح (مثل +9665xxxxxxxx).")
        return redirect("accounts:register")

    if User.objects.filter(email=email).exists():
        messages.error(request, "البريد الإلكتروني مسجل مسبقًا.")
        return redirect("accounts:register")

    # individual
    full_name = (request.POST.get("full_name") or "").strip()
    national_id = (request.POST.get("national_id") or "").strip()
    region_id_individual = (request.POST.get("region_id") or "").strip()
    is_affiliated = (request.POST.get("is_affiliated") or "") in ("on", "true", "1")
    org_branch_id = (request.POST.get("org_branch_id") or "").strip()

    # org
    organization_name = (request.POST.get("organization_name") or "").strip()
    representative_name = (request.POST.get("representative_name") or "").strip()
    region_id_org = (request.POST.get("org_region_id") or request.POST.get("region_id") or "").strip()
    lat = _safe_decimal(request.POST.get("latitude") or "")
    lng = _safe_decimal(request.POST.get("longitude") or "")
    landmark = (request.POST.get("landmark") or "").strip()

    if account_type == "individual":
        if not full_name or not national_id or not region_id_individual:
            messages.error(request, "فضلاً أكمل بيانات الفرد (الاسم الكامل/رقم الهوية/المنطقة).")
            return redirect("accounts:register")
        if not SA_NATIONAL_ID_RE.match(national_id):
            messages.error(request, "رقم الهوية يجب أن يكون 10 أرقام.")
            return redirect("accounts:register")
        if is_affiliated and not org_branch_id:
            messages.error(request, "اختر الجهة لأنك اخترت (تابع لجهة).")
            return redirect("accounts:register")
        if not _validate_region_id(region_id_individual):
            messages.error(request, "المنطقة غير صحيحة.")
            return redirect("accounts:register")

    if account_type == "org":
        if not organization_name or not representative_name:
            messages.error(request, "فضلاً أكمل بيانات الجهة (اسم الجهة/اسم ممثل الجهة).")
            return redirect("accounts:register")
        if not _validate_region_id(region_id_org):
            messages.error(request, "فضلاً اختر المنطقة للجهة.")
            return redirect("accounts:register")
        if lat is None or lng is None:
            messages.error(request, "فضلاً اختر موقع الجهة من الخريطة.")
            return redirect("accounts:register")

    try:
        with transaction.atomic():
            user = User.objects.create_user(email=email, password=password, is_active=False)
            user.phone = phone

            if account_type == "individual":
                user.role = UserRole.INDIVIDUAL
                user.region_id = _validate_region_id(region_id_individual) or 0
                if is_affiliated:
                    user.org_branch_id = int(org_branch_id)
                user.save()
                IndividualProfile.objects.create(
                    user=user,
                    full_name=full_name,
                    national_id=national_id,
                    is_affiliated=is_affiliated,
                )
            else:
                user.role = UserRole.ORG_REP
                user.region_id = _validate_region_id(region_id_org) or 0
                user.save()
                OrganizationProfile.objects.create(
                    user=user,
                    organization_name=organization_name,
                    representative_name=representative_name,
                    latitude=lat,
                    longitude=lng,
                    landmark=landmark,
                )

            otp = EmailOTP.create_otp(email=user.email, purpose="verify_email", ttl_minutes=OTP_TTL_MINUTES)
            _send_verify_email_otp(user.email, otp.code)
            _mark_otp_sent_now(request)

        request.session["pending_verify_email"] = user.email
        messages.success(request, "تم إنشاء الحساب. تم إرسال رمز التفعيل إلى بريدك.")
        return redirect("accounts:verify_email")

    except IntegrityError:
        messages.error(request, "تعذر إنشاء الحساب (قد يكون البريد مسجل).")
        return redirect("accounts:register")
    except Exception as e:
        logger.exception("Register failed: %s", e)
        messages.error(request, "حدث خطأ أثناء التسجيل. حاول مرة أخرى.")
        return redirect("accounts:register")


# -----------------------------
# Verify Email
# -----------------------------
@require_http_methods(["GET", "POST"])
def verify_email_view(request):
    email = (request.session.get("pending_verify_email") or "").strip().lower()
    if not email:
        messages.error(request, "لا يوجد حساب بانتظار التفعيل.")
        return redirect("accounts:register")

    if request.method == "GET":
        return render(request, "accounts_temp/verify_email.html", {"email": email})

    code = (request.POST.get("code") or "").strip()
    if not code:
        messages.error(request, "أدخل رمز التفعيل.")
        return redirect("accounts:verify_email")

    otp = EmailOTP.objects.filter(email=email, purpose="verify_email", is_used=False).order_by("-created_at").first()
    if not otp:
        messages.error(request, "رمز غير صحيح أو تم استخدامه.")
        return redirect("accounts:verify_email")
    if otp.is_expired():
        messages.error(request, "انتهت صلاحية الرمز. اطلب رمزًا جديدًا.")
        return redirect("accounts:verify_email")

    otp.attempts += 1
    otp.save(update_fields=["attempts"])
    if otp.attempts > OTP_MAX_ATTEMPTS:
        messages.error(request, "تم تجاوز عدد المحاولات. اطلب رمزًا جديدًا.")
        return redirect("accounts:verify_email")

    if otp.code != code:
        messages.error(request, "الرمز غير صحيح.")
        return redirect("accounts:verify_email")

    try:
        with transaction.atomic():
            otp.is_used = True
            otp.save(update_fields=["is_used"])
            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, "الحساب غير موجود.")
                return redirect("accounts:register")
            user.is_active = True
            user.save(update_fields=["is_active"])

        request.session.pop("pending_verify_email", None)
        messages.success(request, "تم تفعيل الحساب بنجاح. يمكنك تسجيل الدخول الآن.")
        return redirect("accounts:login")
    except Exception as e:
        logger.exception("Verify email failed: %s", e)
        messages.error(request, "حدث خطأ أثناء التفعيل. حاول مرة أخرى.")
        return redirect("accounts:verify_email")


# -----------------------------
# Resend Verify OTP
# -----------------------------
@require_http_methods(["POST"])
def resend_otp_view(request):
    email = (request.session.get("pending_verify_email") or "").strip().lower()
    if not email:
        messages.error(request, "لا يوجد حساب بانتظار التفعيل.")
        return redirect("accounts:register")

    if not _rate_limit_resend_ok(request):
        messages.error(request, f"انتظر قليلًا قبل إعادة الإرسال ({OTP_RESEND_COOLDOWN_SECONDS} ثانية).")
        return redirect("accounts:verify_email")

    user = User.objects.filter(email=email).first()
    if not user:
        messages.error(request, "الحساب غير موجود.")
        return redirect("accounts:register")

    if user.is_active:
        messages.success(request, "الحساب مفعل بالفعل. يمكنك تسجيل الدخول.")
        request.session.pop("pending_verify_email", None)
        return redirect("accounts:login")

    try:
        otp = EmailOTP.create_otp(email=email, purpose="verify_email", ttl_minutes=OTP_TTL_MINUTES)
        _send_verify_email_otp(email, otp.code)
        _mark_otp_sent_now(request)
        messages.success(request, "تم إرسال رمز جديد إلى بريدك.")
        return redirect("accounts:verify_email")
    except Exception as e:
        logger.exception("Resend OTP failed: %s", e)
        messages.error(request, "تعذر إرسال الرمز الآن. حاول لاحقًا.")
        return redirect("accounts:verify_email")


# -----------------------------
# Login (✅ نفس بوابة الدخول: فرد/جهة/مسؤول + OTP)
# -----------------------------
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "GET":
        return render(request, "accounts_temp/login.html")

    email = (request.POST.get("email") or "").strip().lower()
    password = (request.POST.get("password") or "").strip()

    if not email or not password:
        messages.error(request, "أدخل البريد وكلمة المرور.")
        return redirect("accounts:login")

    user = authenticate(request, email=email, password=password)
    if user is None:
        messages.error(request, "بيانات الدخول غير صحيحة.")
        return redirect("accounts:login")

    if not user.is_active:
        request.session["pending_verify_email"] = user.email
        messages.error(request, "حسابك غير مفعل. أدخل رمز التفعيل.")
        return redirect("accounts:verify_email")

    # ✅ السماح أيضاً للمسؤولين (نفس الهوم)
    if getattr(user, "role", None) not in ALLOWED_PORTAL_ROLES:
        messages.error(request, "غير مصرح لك بالدخول.")
        return redirect("accounts:login")

    try:
        try:
            request.session.cycle_key()
        except Exception:
            pass

        login_email = _clean_and_validate_email(getattr(user, "email", "") or email)
        otp = EmailOTP.create_otp(email=login_email, purpose="login", ttl_minutes=OTP_TTL_MINUTES)

        _send_login_otp_email(login_email, otp.code)
        _mark_otp_login_sent_now(request)

        request.session["pending_login_user_id"] = user.pk
        request.session["pending_login_email"] = login_email

        messages.info(request, "تم إرسال رمز تحقق إلى بريدك. أدخله لإكمال تسجيل الدخول.")
        return redirect("accounts:login_otp")

    except Exception as e:
        logger.exception("Login OTP send failed: %s", e)
        messages.error(request, "تعذر إرسال رمز التحقق الآن. حاول لاحقًا.")
        return redirect("accounts:login")


# -----------------------------
# Login OTP
# -----------------------------
@require_http_methods(["GET", "POST"])
def login_otp_view(request):
    email = (request.session.get("pending_login_email") or "").strip().lower()
    user_id = request.session.get("pending_login_user_id")

    if not email or not user_id:
        messages.error(request, "لا يوجد تسجيل دخول بانتظار التحقق.")
        return redirect("accounts:login")

    try:
        email = _clean_and_validate_email(email)
    except Exception:
        messages.error(request, "البريد الإلكتروني غير صالح.")
        return redirect("accounts:login")

    if request.method == "GET":
        return render(request, "accounts_temp/login_otp.html", {"email": email})

    code = (request.POST.get("code") or "").strip()
    if not code:
        messages.error(request, "أدخل رمز التحقق.")
        return redirect("accounts:login_otp")

    otp = EmailOTP.objects.filter(email=email, purpose="login", is_used=False).order_by("-created_at").first()
    if not otp:
        messages.error(request, "رمز غير صحيح أو تم استخدامه.")
        return redirect("accounts:login_otp")
    if otp.is_expired():
        messages.error(request, "انتهت صلاحية الرمز. اطلب رمزًا جديدًا.")
        return redirect("accounts:login_otp")

    otp.attempts += 1
    otp.save(update_fields=["attempts"])
    if otp.attempts > OTP_MAX_ATTEMPTS:
        messages.error(request, "تم تجاوز عدد المحاولات. اطلب رمزًا جديدًا.")
        return redirect("accounts:login_otp")

    if otp.code != code:
        messages.error(request, "الرمز غير صحيح.")
        return redirect("accounts:login_otp")

    try:
        otp.is_used = True
        otp.save(update_fields=["is_used"])

        user = User.objects.filter(pk=user_id, email=email).first()
        if not user:
            messages.error(request, "الحساب غير موجود.")
            return redirect("accounts:login")

        # ✅ السماح أيضاً للمسؤولين
        if getattr(user, "role", None) not in ALLOWED_PORTAL_ROLES:
            messages.error(request, "غير مصرح لك بالدخول.")
            return redirect("accounts:login")

        login(request, user)

        display_name = _get_display_name(user)
        request.session["display_name"] = display_name

        # ✅ Toast مرة واحدة بعد الدخول
        request.session["show_login_toast"] = True

        # (اختياري) مودال للأفراد فقط كما كان
        if getattr(user, "role", None) == UserRole.INDIVIDUAL:
            request.session["show_welcome_modal"] = True
            request.session["welcome_name"] = display_name

        request.session.pop("pending_login_user_id", None)
        request.session.pop("pending_login_email", None)

        messages.success(request, "تم تسجيل الدخول بنجاح.")

        # ✅ توجيه حسب الدور (فرد/جهة/مسؤول)
        return _redirect_by_role(request, user)

    except Exception as e:
        logger.exception("Login OTP verify failed: %s", e)
        messages.error(request, "حدث خطأ أثناء التحقق. حاول مرة أخرى.")
        return redirect("accounts:login_otp")


# -----------------------------
# Resend Login OTP
# -----------------------------
@require_http_methods(["POST"])
def resend_login_otp_view(request):
    email = (request.session.get("pending_login_email") or "").strip().lower()
    user_id = request.session.get("pending_login_user_id")

    if not email or not user_id:
        messages.error(request, "لا يوجد تسجيل دخول بانتظار التحقق.")
        return redirect("accounts:login")

    try:
        email = _clean_and_validate_email(email)
    except Exception:
        messages.error(request, "البريد الإلكتروني غير صالح.")
        return redirect("accounts:login")

    if not _rate_limit_resend_ok_login(request):
        messages.error(request, f"انتظر قليلًا قبل إعادة الإرسال ({OTP_RESEND_COOLDOWN_SECONDS} ثانية).")
        return redirect("accounts:login_otp")

    user = User.objects.filter(pk=user_id, email=email).first()
    if not user:
        messages.error(request, "الحساب غير موجود.")
        return redirect("accounts:login")

    # ✅ لا نرسل OTP لأدوار غير مسموحة
    if getattr(user, "role", None) not in ALLOWED_PORTAL_ROLES:
        messages.error(request, "غير مصرح لك بالدخول.")
        return redirect("accounts:login")

    try:
        otp = EmailOTP.create_otp(email=email, purpose="login", ttl_minutes=OTP_TTL_MINUTES)
        _send_login_otp_email(email, otp.code)
        _mark_otp_login_sent_now(request)
        messages.success(request, "تم إرسال رمز جديد إلى بريدك.")
        return redirect("accounts:login_otp")
    except Exception as e:
        logger.exception("Resend login OTP failed: %s", e)
        messages.error(request, "تعذر إرسال الرمز الآن. حاول لاحقًا.")
        return redirect("accounts:login_otp")


# -----------------------------
# Logout (POST only ✅)
# -----------------------------
@require_POST
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)

    request.session.pop("display_name", None)
    request.session.pop("show_welcome_modal", None)
    request.session.pop("welcome_name", None)
    request.session.pop("show_login_toast", None)
    request.session.pop("pending_login_user_id", None)
    request.session.pop("pending_login_email", None)

    messages.success(request, "تم تسجيل الخروج بنجاح.")
    return redirect("home")


# -----------------------------
# Clear welcome modal + toast (AJAX)
# -----------------------------
@require_POST
def clear_welcome_view(request):
    request.session.pop("show_welcome_modal", None)
    request.session.pop("welcome_name", None)
    request.session.pop("show_login_toast", None)
    return JsonResponse({"ok": True})
