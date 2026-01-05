from django.contrib import admin
from .models import TrainerProfile

@admin.register(TrainerProfile)
class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "get_region",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )

    @admin.display(description="المنطقة")
    def get_region(self, obj):
        return getattr(obj.user, "region", "—")
