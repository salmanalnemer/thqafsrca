# accounts/urls.py
from django.urls import path
from .views import register_view, login_view, verify_email_view, resend_otp_view

app_name = "accounts"

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("verify-email/", verify_email_view, name="verify_email"),
    path("verify-email/resend/", resend_otp_view, name="resend_otp"),
]
