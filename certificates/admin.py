from django.contrib import admin
from .models import CertificateTemplate, Certificate, CertificateVerification


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "region", "is_active", "created_at")
    list_display_links = ("id", "name")
    list_filter = ("is_active", "region")
    search_fields = ("name", "region__name")
    ordering = ("-id",)
    readonly_fields = ("created_at",)
    autocomplete_fields = ("region",)

    fieldsets = (
        ("بيانات القالب", {"fields": ("name", "region", "is_active")}),
        ("معلومات النظام", {"fields": ("created_at",)}),
    )


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("id", "serial_number", "enrollment", "issued_at", "issued_by", "created_at")
    list_display_links = ("id", "serial_number")
    list_filter = ("issued_at", "enrollment__course__region")
    search_fields = (
        "serial_number",
        "enrollment__course__title",
        "enrollment__individual__full_name",
        "enrollment__individual__email",
    )
    ordering = ("-id",)
    readonly_fields = ("created_at",)

    autocomplete_fields = ("enrollment", "template", "issued_by")

    fieldsets = (
        ("بيانات الشهادة", {"fields": ("serial_number", "enrollment", "template")}),
        ("الإصدار", {"fields": ("issued_at", "issued_by")}),
        ("معلومات النظام", {"fields": ("created_at",)}),
    )


@admin.register(CertificateVerification)
class CertificateVerificationAdmin(admin.ModelAdmin):
    list_display = ("id", "certificate", "token", "public_lookup_enabled", "created_at")
    list_display_links = ("id", "certificate")
    list_filter = ("public_lookup_enabled",)
    search_fields = ("token", "certificate__serial_number")
    ordering = ("-id",)
    readonly_fields = ("created_at",)

    autocomplete_fields = ("certificate",)

    fieldsets = (
        ("بيانات التحقق", {"fields": ("certificate", "token", "public_lookup_enabled")}),
        ("معلومات النظام", {"fields": ("created_at",)}),
    )
