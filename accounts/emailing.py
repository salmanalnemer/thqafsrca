from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils import timezone


def send_verify_email(*, request, to_email: str, otp_code: str, ttl_minutes: int = 10, user_name: str | None = None) -> None:
    """
    إرسال رسالة تفعيل البريد عبر OTP.
    - يستخدم HTML + Plain text
    - يبني رابط الشعار بشكل absolute
    """
    logo_url = request.build_absolute_uri(static("assets/img/logothqaf.png"))

    subject = "تفعيل حسابك في بوابة ثقف | تصرف سريع ينقذ حياة"

    ctx = {
        "otp_code": otp_code,
        "ttl_minutes": ttl_minutes,
        "user_name": user_name or "بك",
        "logo_url": logo_url,
        "year": timezone.now().year,
    }

    text_body = render_to_string("emails/verify_email.txt", ctx)
    html_body = render_to_string("emails/verify_email.html", ctx)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)
