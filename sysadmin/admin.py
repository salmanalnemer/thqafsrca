from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "actor", "target_user", "ip_address")
    list_filter = ("action", "created_at")
    search_fields = ("actor__email", "target_user__email", "ip_address", "note")
    readonly_fields = ("actor", "action", "target_user", "ip_address", "user_agent", "before", "after", "note", "created_at")
