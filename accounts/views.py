# accounts/views.py
from __future__ import annotations

import logging
import re
import secrets
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import EmailOTP, IndividualProfile, OrganizationProfile, User, UserRole

logger = logging.getLogger(__name__)

SA_NATIONAL_ID_RE = re.compile(r"^\d{10}$")
PHONE_RE = re.compile(r"^\+?\d{8,15}$")

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 6
OTP_RESEND_COOLDOWN_SECONDS = 60  # لا يسمح بإعادة الإرسال قبل مرور 60 ثانية


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


def _send_otp_email(email: str, code: str) -> None:
    """
    يرسل رمز التفعيل عبر البريد.
    يعتمد على إعدادات EMAIL_* في settings.py.
    """
    subject = "رمز تفعيل الحساب - ثقف"

    body = (
        "مرحبًا،\n\n"
        f"رمز تفعيل حسابك هو: {code}\n"
        f"صلاحية الرمز: {OTP_TTL_MINUTES} دقائق.\n\n"
        "إذا لم تطلب هذا الرمز، تجاهل الرسالة.\n"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
    if not from_email:
        # لو ما تم ضبط from_email، نخليها واضحة في اللوج بدل ما تتكسر بصمت
        logger.warning("DEFAULT_FROM_EMAIL / EMAIL_HOST_USER is not configured.")
        from_email = "no-reply@localhost"

    send_mail(
        subject=subject,
        message=body,
        from_email=from_email,
        recipient_list=[email],
        fail_silently=False,
    )


def _get_regions_and_org_branches():
    regions = []
    org_branches = []

    try:
        from regions.models import Region  # type: ignore

        regions = Region.objects.all().order_by("id")
    except Exception as e:
        logger.warning("Could not load regions: %s", e)
        regions = []

    try:
        from organizations.models import OrganizationBranch  # type: ignore

        org_branches = OrganizationBranch.objects.all().order_by("id")
    except Exception as e:
        logger.warning("Could not load organization branches: %s", e)
        org_branches = []

    return regions, org_branches


def _rate_limit_resend_ok(request) -> bool:
    """
    يمنع إعادة إرسال OTP بشكل سريع (بسيط بالجلسة).
    """
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


# -----------------------------
# Register (Individuals + Orgs)
# -----------------------------
@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == "GET":
        regions, org_branches = _get_regions_and_org_branches()
        return render(
            request,
            "accounts_temp/register.html",
            {"regions": regions, "org_branches": org_branches},
        )

    # POST
    account_type = (request.POST.get("account_type") or "").strip()  # "individual" | "org"

    email = (request.POST.get("email") or "").strip().lower()
    phone = (request.POST.get("phone") or "").strip()
    password = (request.POST.get("password") or "").strip()
    confirm_password = (request.POST.get("confirm_password") or "").strip()

    if account_type not in ("individual", "org"):
        messages.error(request, "نوع التسجيل غير صحيح.")
        return redirect("register")

    if not email or not phone or not password or not confirm_password:
        messages.error(request, "فضلاً أكمل جميع الحقول المطلوبة.")
        return redirect("register")

    if password != confirm_password:
        messages.error(request, "كلمتا المرور غير متطابقتين.")
        return redirect("register")

    if not PHONE_RE.match(phone):
        messages.error(request, "رقم الجوال غير صحيح (مثل +9665xxxxxxxx).")
        return redirect("register")

    if User.objects.filter(email=email).exists():
        messages.error(request, "البريد الإلكتروني مسجل مسبقًا.")
        return redirect("register")

    # ---------- Individual fields ----------
    full_name = (request.POST.get("full_name") or "").strip()
    national_id = (request.POST.get("national_id") or "").strip()
    region_id_individual = (request.POST.get("region_id") or "").strip()

    is_affiliated = (request.POST.get("is_affiliated") or "") in ("on", "true", "1")
    org_branch_id = (request.POST.get("org_branch_id") or "").strip()

    # ---------- Organization fields ----------
    organization_name = (request.POST.get("organization_name") or "").strip()
    representative_name = (request.POST.get("representative_name") or "").strip()

    # ✅ المنطقة للجهات (مضافة)
    region_id_org = (request.POST.get("org_region_id") or request.POST.get("region_id") or "").strip()

    lat = _safe_decimal(request.POST.get("latitude") or "")
    lng = _safe_decimal(request.POST.get("longitude") or "")
    landmark = (request.POST.get("landmark") or "").strip()

    # Validate per account type
    if account_type == "individual":
        if not full_name or not national_id or not region_id_individual:
            messages.error(request, "فضلاً أكمل بيانات الفرد (الاسم الكامل/رقم الهوية/المنطقة).")
            return redirect("register")

        if not SA_NATIONAL_ID_RE.match(national_id):
            messages.error(request, "رقم الهوية يجب أن يكون 10 أرقام.")
            return redirect("register")

        if is_affiliated and not org_branch_id:
            messages.error(request, "اختر الجهة لأنك اخترت (تابع لجهة).")
            return redirect("register")

        rid = _validate_region_id(region_id_individual)
        if not rid:
            messages.error(request, "المنطقة غير صحيحة.")
            return redirect("register")

    if account_type == "org":
        if not organization_name or not representative_name:
            messages.error(request, "فضلاً أكمل بيانات الجهة (اسم الجهة/اسم ممثل الجهة).")
            return redirect("register")

        # ✅ المنطقة مطلوبة للجهات
        rid = _validate_region_id(region_id_org)
        if not rid:
            messages.error(request, "فضلاً اختر المنطقة للجهة.")
            return redirect("register")

        # الموقع مطلوب حسب طلبك
        if lat is None or lng is None:
            messages.error(request, "فضلاً اختر موقع الجهة من الخريطة.")
            return redirect("register")

    # Create user + profile + otp
    try:
        with transaction.atomic():
            user = User.objects.create_user(email=email, password=password, is_active=False)

            # common
            user.phone = phone

            if account_type == "individual":
                user.role = UserRole.INDIVIDUAL

                rid = _validate_region_id(region_id_individual)
                if not rid:
                    raise ValueError("Invalid region_id for individual")
                user.region_id = rid

                if is_affiliated:
                    try:
                        user.org_branch_id = int(org_branch_id)
                    except Exception:
                        messages.error(request, "الجهة غير صحيحة.")
                        raise ValueError("Invalid org_branch_id")

                user.save()

                IndividualProfile.objects.create(
                    user=user,
                    full_name=full_name,
                    national_id=national_id,
                    is_affiliated=is_affiliated,
                )

            else:
                user.role = UserRole.ORG_REP

                rid = _validate_region_id(region_id_org)
                if not rid:
                    raise ValueError("Invalid region_id for org")
                user.region_id = rid

                user.save()

                OrganizationProfile.objects.create(
                    user=user,
                    organization_name=organization_name,
                    representative_name=representative_name,
                    latitude=lat,
                    longitude=lng,
                    landmark=landmark,
                )

            # OTP
            otp = EmailOTP.create_otp(
                email=user.email,
                purpose="verify_email",
                ttl_minutes=OTP_TTL_MINUTES,
            )

            # ارسال
            _send_otp_email(user.email, otp.code)
            _mark_otp_sent_now(request)

        request.session["pending_verify_email"] = user.email
        messages.success(request, "تم إنشاء الحساب. تم إرسال رمز التفعيل إلى بريدك.")
        return redirect("verify_email")

    except IntegrityError:
        messages.error(request, "تعذر إنشاء الحساب (قد يكون البريد مسجل).")
        return redirect("register")
    except Exception as e:
        logger.exception("Register failed: %s", e)
        if not any(m.message for m in messages.get_messages(request)):
            messages.error(request, "حدث خطأ أثناء التسجيل. حاول مرة أخرى.")
        return redirect("register")


# -----------------------------
# Verify Email OTP
# -----------------------------
@require_http_methods(["GET", "POST"])
def verify_email_view(request):
    email = (request.session.get("pending_verify_email") or "").strip().lower()
    if not email:
        messages.error(request, "لا يوجد حساب بانتظار التفعيل.")
        return redirect("register")

    if request.method == "GET":
        return render(request, "accounts_temp/verify_email.html", {"email": email})

    # POST
    code = (request.POST.get("code") or "").strip()

    if not code:
        messages.error(request, "أدخل رمز التفعيل.")
        return redirect("verify_email")

    otp = (
        EmailOTP.objects.filter(email=email, purpose="verify_email", is_used=False)
        .order_by("-created_at")
        .first()
    )

    if not otp:
        messages.error(request, "رمز غير صحيح أو تم استخدامه.")
        return redirect("verify_email")

    if otp.is_expired():
        messages.error(request, "انتهت صلاحية الرمز. اطلب رمزًا جديدًا.")
        return redirect("verify_email")

    # Increase attempts (brute-force protection)
    otp.attempts += 1
    otp.save(update_fields=["attempts"])

    if otp.attempts > OTP_MAX_ATTEMPTS:
        messages.error(request, "تم تجاوز عدد المحاولات. اطلب رمزًا جديدًا.")
        return redirect("verify_email")

    if otp.code != code:
        messages.error(request, "الرمز غير صحيح.")
        return redirect("verify_email")

    # success
    try:
        with transaction.atomic():
            otp.is_used = True
            otp.save(update_fields=["is_used"])

            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, "الحساب غير موجود.")
                return redirect("register")

            user.is_active = True
            user.save(update_fields=["is_active"])

        request.session.pop("pending_verify_email", None)
        messages.success(request, "تم تفعيل الحساب بنجاح. يمكنك تسجيل الدخول الآن.")
        return redirect("login")

    except Exception as e:
        logger.exception("Verify email failed: %s", e)
        messages.error(request, "حدث خطأ أثناء التفعيل. حاول مرة أخرى.")
        return redirect("verify_email")


# -----------------------------
# Resend OTP
# -----------------------------
@require_http_methods(["POST"])
def resend_otp_view(request):
    email = (request.session.get("pending_verify_email") or "").strip().lower()
    if not email:
        messages.error(request, "لا يوجد حساب بانتظار التفعيل.")
        return redirect("register")

    if not _rate_limit_resend_ok(request):
        messages.error(request, f"انتظر قليلًا قبل إعادة الإرسال ({OTP_RESEND_COOLDOWN_SECONDS} ثانية).")
        return redirect("verify_email")

    user = User.objects.filter(email=email).first()
    if not user:
        messages.error(request, "الحساب غير موجود.")
        return redirect("register")

    if user.is_active:
        messages.success(request, "الحساب مفعل بالفعل. يمكنك تسجيل الدخول.")
        request.session.pop("pending_verify_email", None)
        return redirect("login")

    try:
        otp = EmailOTP.create_otp(email=email, purpose="verify_email", ttl_minutes=OTP_TTL_MINUTES)
        _send_otp_email(email, otp.code)
        _mark_otp_sent_now(request)
        messages.success(request, "تم إرسال رمز جديد إلى بريدك.")
        return redirect("verify_email")
    except Exception as e:
        logger.exception("Resend OTP failed: %s", e)
        messages.error(request, "تعذر إرسال الرمز الآن. حاول لاحقًا.")
        return redirect("verify_email")


# -----------------------------
# Login
# -----------------------------
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "GET":
        return render(request, "accounts_temp/login.html")

    email = (request.POST.get("email") or "").strip().lower()
    password = (request.POST.get("password") or "").strip()

    if not email or not password:
        messages.error(request, "أدخل البريد وكلمة المرور.")
        return redirect("login")

    user = authenticate(request, email=email, password=password)
    if user is None:
        messages.error(request, "بيانات الدخول غير صحيحة.")
        return redirect("login")

    if not user.is_active:
        request.session["pending_verify_email"] = user.email
        messages.error(request, "حسابك غير مفعل. أدخل رمز التفعيل.")
        return redirect("verify_email")

    login(request, user)
    return redirect("home")
