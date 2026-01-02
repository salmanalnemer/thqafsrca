from django.contrib import admin
from .models import OrganizationMaster, OrganizationBranch, OrganizationRepresentative


@admin.register(OrganizationMaster)
class OrganizationMasterAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "national_id", "is_active", "created_at")
    list_display_links = ("id", "name")
    list_filter = ("is_active",)
    search_fields = ("name", "national_id")
    ordering = ("name",)
    readonly_fields = ("created_at",)

    fieldsets = (
        ("بيانات الجهة الأم", {"fields": ("name", "national_id", "is_active")}),
        ("معلومات النظام", {"fields": ("created_at",)}),
    )


@admin.register(OrganizationBranch)
class OrganizationBranchAdmin(admin.ModelAdmin):
    list_display = ("id", "master", "region", "status", "approved_by", "approved_at", "created_at")
    list_display_links = ("id", "master")
    list_filter = ("status", "region")
    search_fields = ("master__name", "branch_name", "region__name", "phone", "address")
    ordering = ("-id",)
    readonly_fields = ("created_at",)

    autocomplete_fields = ("master", "region", "approved_by")

    fieldsets = (
        ("بيانات الفرع", {"fields": ("master", "region", "branch_name", "address", "phone")}),
        ("حالة الاعتماد", {"fields": ("status", "approved_by", "approved_at", "notes")}),
        ("معلومات النظام", {"fields": ("created_at",)}),
    )


@admin.register(OrganizationRepresentative)
class OrganizationRepresentativeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "org_branch", "is_primary", "created_at")
    list_display_links = ("id", "user")
    list_filter = ("is_primary",)
    search_fields = ("user__email", "org_branch__master__name", "org_branch__region__name")
    ordering = ("-id",)
    readonly_fields = ("created_at",)

    autocomplete_fields = ("user", "org_branch")

    fieldsets = (
        ("بيانات ممثل الجهة", {"fields": ("user", "org_branch", "is_primary")}),
        ("معلومات النظام", {"fields": ("created_at",)}),
    )
