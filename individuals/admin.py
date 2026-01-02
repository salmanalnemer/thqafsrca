from django.contrib import admin
from .models import Individual


@admin.register(Individual)
class IndividualAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "email",
        "phone",
        "region",
        "org_branch",
        "employee_id",
        "is_active",
        "created_at",
    )
    list_display_links = ("id", "full_name")
    list_filter = ("is_active", "region")
    search_fields = ("full_name", "email", "phone", "national_id", "employee_id")
    ordering = ("-id",)
    readonly_fields = ("created_at",)

    autocomplete_fields = ("region", "org_branch")

    fieldsets = (
        ("بيانات الفرد", {"fields": ("full_name", "national_id", "email", "phone")}),
        ("المنطقة والجهة", {"fields": ("region", "org_branch", "employee_id")}),
        ("الحالة", {"fields": ("is_active",)}),
        ("معلومات النظام", {"fields": ("created_at",)}),
    )
