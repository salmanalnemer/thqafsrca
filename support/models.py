from __future__ import annotations

from django.conf import settings
from django.db import models


class TicketPriority(models.TextChoices):
    LOW = "low", "منخفض"
    MEDIUM = "medium", "متوسط"
    HIGH = "high", "مرتفع"
    URGENT = "urgent", "عاجل"


class TicketStatus(models.TextChoices):
    OPEN = "open", "مفتوح"
    IN_PROGRESS = "in_progress", "قيد المعالجة"
    WAITING_USER = "waiting_user", "بانتظار المستخدم"
    ESCALATED = "escalated", "مصعد"
    RESOLVED = "resolved", "محلول"
    CLOSED = "closed", "مغلق"


class TicketCategory(models.TextChoices):
    ACCOUNT = "account", "الحساب"
    COURSES = "courses", "الدورات"
    CERTIFICATES = "certificates", "الشهادات"
    ORGANIZATIONS = "organizations", "الجهات"
    TECHNICAL = "technical", "تقني"
    OTHER = "other", "أخرى"


class SupportTicket(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="support_tickets",
    )

    # قد يفيد للتوجيه/التقارير
    region = models.ForeignKey("regions.Region", on_delete=models.SET_NULL, null=True, blank=True, related_name="support_tickets")

    title = models.CharField(max_length=200)
    description = models.TextField()

    category = models.CharField(max_length=20, choices=TicketCategory.choices, default=TicketCategory.TECHNICAL, db_index=True)
    priority = models.CharField(max_length=10, choices=TicketPriority.choices, default=TicketPriority.MEDIUM, db_index=True)
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN, db_index=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )

    escalation_level = models.PositiveIntegerField(default=0)  # 0 = لا يوجد، 1+ تصعيد
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["category", "status"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"


class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_messages")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Msg on #{self.ticket_id}"


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_attachments")

    # مبدئيًا: مسار ملف (لاحقًا نربطه بـ FileField في إعدادات media)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name
