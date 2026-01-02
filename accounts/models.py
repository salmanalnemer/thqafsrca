from __future__ import annotations

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class UserRole(models.TextChoices):
    SUPER_ADMIN = "super_admin", "مدير عام"
    REGION_MANAGER = "region_manager", "مدير إدارة منطقة"
    SUPERVISOR = "supervisor", "مشرف (نائب)"
    COORDINATOR = "coordinator", "منسق الدورات"
    ORG_REP = "org_rep", "ممثل جهة"
    INDIVIDUAL = "individual", "فرد"


class User(AbstractUser):
    """
    Custom user:
    - Uses email as the login identifier
    - Can be scoped to: region / org_branch / individual
    """

    username = models.CharField(max_length=150, blank=True, null=True)  # لا نعتمد عليه للدخول
    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=32,
        choices=UserRole.choices,
        default=UserRole.INDIVIDUAL,
        db_index=True,
    )

    phone_validator = RegexValidator(
        regex=r"^\+?\d{8,15}$",
        message="رقم الهاتف يجب أن يكون بصيغة دولية مثل +9665xxxxxxxx",
    )
    phone = models.CharField(max_length=20, blank=True, validators=[phone_validator])

    # نطاق المستخدم (Scope) — روابط اختيارية لتحديد ماذا يرى
    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    org_branch = models.ForeignKey(
        "organizations.OrganizationBranch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    individual = models.OneToOneField(
        "individuals.Individual",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_account",
    )

    # تعقب
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # لا نطلب username

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"


class EmailOTP(models.Model):
    """
    OTP via email for login/verification.
    """
    PURPOSE_CHOICES = (
        ("login", "تسجيل الدخول"),
        ("verify_email", "تفعيل البريد"),
        ("reset_password", "استعادة كلمة المرور"),
    )

    email = models.EmailField(db_index=True)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default="login")
    code = models.CharField(max_length=10, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["email", "purpose", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]

    @staticmethod
    def generate_code(length: int = 6) -> str:
        # كود رقمي بسيط
        digits = "0123456789"
        return "".join(secrets.choice(digits) for _ in range(length))

    @classmethod
    def create_otp(cls, email: str, purpose: str = "login", ttl_minutes: int = 10) -> "EmailOTP":
        now = timezone.now()
        return cls.objects.create(
            email=email.lower(),
            purpose=purpose,
            code=cls.generate_code(6),
            expires_at=now + timedelta(minutes=ttl_minutes),
        )

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"OTP {self.email} ({self.purpose})"
