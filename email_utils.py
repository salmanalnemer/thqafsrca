from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection


def _smtp_connection(username: str, password: str):
    return get_connection(
        backend=settings.EMAIL_BACKEND,
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=username,
        password=password,
        use_ssl=True if settings.EMAIL_PORT == 465 else settings.EMAIL_USE_SSL,
        use_tls=False if settings.EMAIL_PORT == 465 else settings.EMAIL_USE_TLS,
        timeout=getattr(settings, "EMAIL_TIMEOUT", 20),
        fail_silently=getattr(settings, "EMAIL_FAIL_SILENTLY", False),
    )


def send_no_reply_email(*, subject: str, html_content: str, to: str) -> None:
    """
    OTP + إشعارات الدورات (no-reply)
    """
    conn = _smtp_connection(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

    from_email = f"{settings.THQAF_EMAIL_FROM_NAME} <{settings.THQAF_NO_REPLY_EMAIL}>"

    msg = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=from_email,
        to=[to],
        connection=conn,
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


def send_support_email(
    *, subject: str, html_content: str, to: str, reply_to_email: str | None = None
) -> None:
    """
    تواصل معنا (support)
    """
    if not settings.THQAF_SUPPORT_EMAIL_PASSWORD:
        raise RuntimeError("THQAF_SUPPORT_EMAIL_PASSWORD is missing in .env")

    conn = _smtp_connection(settings.THQAF_SUPPORT_EMAIL, settings.THQAF_SUPPORT_EMAIL_PASSWORD)

    from_email = f"{settings.THQAF_SUPPORT_EMAIL_FROM_NAME} <{settings.THQAF_SUPPORT_EMAIL}>"

    msg = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=from_email,
        to=[to],
        connection=conn,
        reply_to=[reply_to_email] if reply_to_email else None,
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)
