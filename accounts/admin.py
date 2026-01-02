from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User, EmailOTP


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    لوحة إدارة المستخدمين (معرّبة)
    """

    # الأعمدة الظاهرة في القائمة
    list_display = (
        "id",
        "email",
        "get_role_display",
        "is_active",
        "is_staff",
        "region",
        "org_branch",
        "created_at",
    )

    list_display_links = ("id", "email")

    # الفلاتر
    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "region",
    )

    # البحث
    search_fields = (
        "email",
        "phone",
        "first_name",
        "last_name",
    )

    ordering = ("-id",)

    # الحقول القابلة للتعديل
    fieldsets = (
        (None, {
            "fields": ("email", "password"),
        }),
        ("البيانات الشخصية", {
            "fields": ("first_name", "last_name", "phone"),
        }),
        ("الدور والنطاق", {
            "fields": ("role", "region", "org_branch", "individual"),
        }),
        ("الصلاحيات الإدارية", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        ("معلومات النظام", {
            "fields": ("last_login", "date_joined", "created_at", "updated_at"),
        }),
    )

    # عند إضافة مستخدم جديد
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "password1",
                "password2",
                "role",
                "is_active",
                "is_staff",
            ),
        }),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "last_login",
        "date_joined",
    )

    # استخدام البريد بدل اسم المستخدم
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "username" in form.base_fields:
            form.base_fields["username"].required = False
            form.base_fields["username"].widget = admin.widgets.AdminTextInputWidget(attrs={"readonly": "readonly"})
        return form

    # تحسين عنوان العمود للدور
    def get_role_display(self, obj):
        return obj.get_role_display()
    get_role_display.short_description = "الدور"


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    """
    إدارة رموز التحقق (OTP)
    """

    list_display = (
        "id",
        "email",
        "purpose",
        "code",
        "is_used",
        "attempts",
        "expires_at",
        "created_at",
    )

    list_display_links = ("id", "email")

    list_filter = (
        "purpose",
        "is_used",
    )

    search_fields = (
        "email",
        "code",
    )

    ordering = ("-id",)

    readonly_fields = (
        "created_at",
    )

    fieldsets = (
        (None, {
            "fields": ("email", "purpose", "code"),
        }),
        ("حالة الرمز", {
            "fields": ("is_used", "attempts", "expires_at"),
        }),
        ("معلومات النظام", {
            "fields": ("created_at",),
        }),
    )
