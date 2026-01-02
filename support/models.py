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
        verbose_name="أنشئت بواسطة",
    )

    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets",
        verbose_name="المنطقة (اختياري)",
    )

    title = models.CharField(max_length=200, verbose_name="عنوان التذكرة")
    description = models.TextField(verbose_name="وصف المشكلة")

    category = models.CharField(
        max_length=20,
        choices=TicketCategory.choices,
        default=TicketCategory.TECHNICAL,
        db_index=True,
        verbose_name="التصنيف",
    )
    priority = models.CharField(
        max_length=10,
        choices=TicketPriority.choices,
        default=TicketPriority.MEDIUM,
        db_index=True,
        verbose_name="الأولوية",
    )
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.OPEN,
        db_index=True,
        verbose_name="الحالة",
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        verbose_name="مسندة إلى (اختياري)",
    )

    escalation_level = models.PositiveIntegerField(default=0, verbose_name="مستوى التصعيد")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ آخر تحديث")

    class Meta:
        verbose_name = "تذكرة دعم"
        verbose_name_plural = "تذاكر الدعم"
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["category", "status"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"


class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages", verbose_name="التذكرة")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_messages", verbose_name="الكاتب")
    message = models.TextField(verbose_name="الرسالة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإرسال")

    class Meta:
        verbose_name = "رسالة تذكرة"
        verbose_name_plural = "رسائل التذاكر"

    def __str__(self):
        return f"رسالة على تذكرة #{self.ticket_id}"


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="attachments", verbose_name="التذكرة")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ticket_attachments", verbose_name="رُفع بواسطة")

    file_name = models.CharField(max_length=255, verbose_name="اسم الملف")
    file_path = models.CharField(max_length=500, verbose_name="مسار الملف")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")

    class Meta:
        verbose_name = "مرفق تذكرة"
        verbose_name_plural = "مرفقات التذاكر"

    def __str__(self):
        return self.file_name
