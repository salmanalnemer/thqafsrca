from django.contrib import admin
from .models import Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "is_active", "created_at", "updated_at")
    list_display_links = ("id", "name")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("بيانات المنطقة", {"fields": ("name", "code", "is_active")}),
        ("معلومات النظام", {"fields": ("created_at", "updated_at")}),
    )
