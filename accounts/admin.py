from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User, EmailOTP


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # عرض أساسي
    list_display = ("id", "email", "role", "is_active", "is_staff", "region", "org_branch", "created_at")
    list_filter = ("role", "is_active", "is_staff", "is_superuser", "region")
    search_fields = ("email", "phone", "first_name", "last_name")
    ordering = ("-id",)

    # استخدم الإيميل بدل اليوزرنيم
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("المعلومات الشخصية", {"fields": ("first_name", "last_name", "phone")}),
        ("النطاق والصلاحيات", {"fields": ("role", "region", "org_branch", "individual")}),
        ("الصلاحيات", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("التواريخ", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role", "is_active", "is_staff"),
        }),
    )

    # لأننا ورثنا AbstractUser، قد يظهر username — نخفيه من لوحة الإضافة/التعديل إن رغبت
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "username" in form.base_fields:
            form.base_fields["username"].required = False
        return form


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "purpose", "code", "is_used", "attempts", "expires_at", "created_at")
    list_filter = ("purpose", "is_used")
    search_fields = ("email", "code")
    ordering = ("-id",)
    readonly_fields = ("created_at",)
