from django.contrib import admin
from .models import AttendanceConfirmation


@admin.register(AttendanceConfirmation)
class AttendanceConfirmationAdmin(admin.ModelAdmin):
    list_display = ("id", "enrollment", "method", "confirmed_at", "created_at")
    list_display_links = ("id", "enrollment")
    list_filter = ("method", "confirmed_at")
    search_fields = (
        "enrollment__course__title",
        "enrollment__individual__full_name",
        "enrollment__individual__email",
        "confirmation_code",
    )
    ordering = ("-id",)
    readonly_fields = ("created_at",)

    autocomplete_fields = ("enrollment",)

    fieldsets = (
        ("بيانات التأكيد", {"fields": ("enrollment", "method", "confirmed_at", "note")}),
        ("بيانات إضافية", {"fields": ("confirmation_code",)}),
        ("معلومات النظام", {"fields": ("created_at",)}),
    )
