from __future__ import annotations

import secrets
from datetime import timedelta
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.conf import settings



class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("البريد الإلكتروني مطلوب")
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
            raise ValueError("يجب أن يكون is_staff=True للمشرف العام.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("يجب أن يكون is_superuser=True للمشرف العام.")
        return self._create_user(email, password, **extra_fields)


class UserRole(models.TextChoices):
    SUPER_ADMIN = "super_admin", "مدير عام"
    REGION_MANAGER = "region_manager", "مدير إدارة منطقة"
    SUPERVISOR = "supervisor", "مشرف (نائب)"
    COORDINATOR = "coordinator", "منسق الدورات"
    TRAINER = "trainer", "مدرب"
    ORG_REP = "org_rep", "ممثل جهة"
    INDIVIDUAL = "individual", "فرد"


class User(AbstractUser):
    """
    مستخدم مخصص:
    - يعتمد البريد الإلكتروني كمعرّف دخول
    - يمكن تقييده بنطاق: منطقة / فرع جهة / فرد
    """

    username = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="اسم المستخدم",
        help_text="اختياري (لا نعتمد عليه للدخول).",
    )

    email = models.EmailField(
        unique=True,
        verbose_name="البريد الإلكتروني",
    )

    role = models.CharField(
        max_length=32,
        choices=UserRole.choices,
        default=UserRole.INDIVIDUAL,
        db_index=True,
        verbose_name="الدور",
    )

    phone_validator = RegexValidator(
        regex=r"^\+?\d{8,15}$",
        message="رقم الهاتف يجب أن يكون بصيغة دولية مثل +9665xxxxxxxx",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[phone_validator],
        verbose_name="رقم الجوال",
    )

    # نطاق المستخدم (Scope)
    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="المنطقة",
    )
    org_branch = models.ForeignKey(
        "organizations.OrganizationBranch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="فرع الجهة",
    )
    individual = models.OneToOneField(
        "individuals.Individual",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_account",
        verbose_name="ملف الفرد",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ آخر تحديث",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "مستخدم"
        verbose_name_plural = "المستخدمون"
        indexes = [
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"


class EmailOTP(models.Model):
    """
    رمز تحقق (OTP) عبر البريد للتسجيل/التفعيل/استعادة كلمة المرور.
    """

    PURPOSE_CHOICES = (
        ("login", "تسجيل الدخول"),
        ("verify_email", "تفعيل البريد"),
        ("reset_password", "استعادة كلمة المرور"),
    )

    email = models.EmailField(
        db_index=True,
        verbose_name="البريد الإلكتروني",
    )
    purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES,
        default="login",
        verbose_name="الغرض",
    )
    code = models.CharField(
        max_length=10,
        db_index=True,
        verbose_name="الرمز",
    )
    expires_at = models.DateTimeField(
        db_index=True,
        verbose_name="ينتهي في",
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name="تم استخدامه",
    )
    attempts = models.PositiveIntegerField(
        default=0,
        verbose_name="عدد المحاولات",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء",
    )

    class Meta:
        verbose_name = "رمز تحقق عبر البريد"
        verbose_name_plural = "رموز التحقق عبر البريد"
        indexes = [
            models.Index(fields=["email", "purpose", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]

    @staticmethod
    def generate_code(length: int = 6) -> str:
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

class IndividualProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="individual_profile",
    )
    full_name = models.CharField(max_length=200, verbose_name="الاسم الكامل")
    national_id = models.CharField(max_length=20, db_index=True, verbose_name="رقم الهوية")
    is_affiliated = models.BooleanField(default=False, verbose_name="تابع لجهة؟")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class OrganizationProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_profile",
    )
    organization_name = models.CharField(max_length=255, verbose_name="اسم الجهة")
    representative_name = models.CharField(max_length=255, verbose_name="اسم ممثل الجهة")

    # موقع بالخريطة
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    landmark = models.CharField(max_length=255, blank=True, verbose_name="إضافة معلم")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.organization_name