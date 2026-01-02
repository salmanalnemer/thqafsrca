from django.contrib import admin
from .models import SupportTicket, TicketMessage, TicketAttachment


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ("created_at",)
    verbose_name = "رد/تعليق"
    verbose_name_plural = "الردود/التعليقات"


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0
    readonly_fields = ("created_at",)
    verbose_name = "مرفق"
    verbose_name_plural = "المرفقات"


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "priority",
        "status",
        "region",
        "created_by",
        "assigned_to",
        "escalation_level",
        "created_at",
    )
    list_display_links = ("id", "title")
    list_filter = ("status", "priority", "category", "region")
    search_fields = ("title", "description", "created_by__email", "assigned_to__email")
    ordering = ("-id",)
    readonly_fields = ("created_at", "updated_at")

    inlines = [TicketMessageInline, TicketAttachmentInline]
    autocomplete_fields = ("created_by", "assigned_to", "region")

    fieldsets = (
        ("بيانات التذكرة", {"fields": ("title", "description", "region")}),
        ("التصنيف والأولوية", {"fields": ("category", "priority", "status")}),
        ("الإسناد والتصعيد", {"fields": ("assigned_to", "escalation_level")}),
        ("معلومات النظام", {"fields": ("created_at", "updated_at")}),
    )
