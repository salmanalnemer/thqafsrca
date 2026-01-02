from __future__ import annotations

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class DeliveryMode(models.TextChoices):
    IN_PERSON = "in_person", "حضوري"
    ONLINE = "online", "عن بعد"
    HYBRID = "hybrid", "مختلط"


class Course(models.Model):
    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.PROTECT,
        related_name="courses",
        verbose_name="المنطقة",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_courses",
        verbose_name="أنشئ بواسطة",
    )

    title = models.CharField(max_length=220, verbose_name="عنوان الدورة")
    description = models.TextField(blank=True, verbose_name="وصف الدورة")
    delivery_mode = models.CharField(
        max_length=20,
        choices=DeliveryMode.choices,
        default=DeliveryMode.IN_PERSON,
        verbose_name="نوع التنفيذ",
    )

    start_at = models.DateTimeField(verbose_name="تاريخ/وقت البداية")
    end_at = models.DateTimeField(verbose_name="تاريخ/وقت النهاية")

    capacity = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="السعة")
    allow_individuals = models.BooleanField(default=True, verbose_name="السماح للأفراد")
    allow_organizations = models.BooleanField(default=True, verbose_name="السماح للجهات")

    is_published = models.BooleanField(default=False, verbose_name="منشورة")
    is_active = models.BooleanField(default=True, verbose_name="نشطة")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "دورة"
        verbose_name_plural = "الدورات"
        indexes = [
            models.Index(fields=["region", "is_published", "start_at"]),
        ]
        ordering = ["-start_at"]

    def __str__(self):
        return f"{self.title} ({self.region.name})"

    @property
    def is_finished(self) -> bool:
        return timezone.now() >= self.end_at


class CourseSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sessions", verbose_name="الدورة")
    title = models.CharField(max_length=200, blank=True, verbose_name="عنوان الجلسة (اختياري)")
    start_at = models.DateTimeField(verbose_name="بداية الجلسة")
    end_at = models.DateTimeField(verbose_name="نهاية الجلسة")

    class Meta:
        verbose_name = "جلسة دورة"
        verbose_name_plural = "جلسات الدورات"

    def __str__(self):
        return f"جلسة - {self.course.title}"


class EnrollmentStatus(models.TextChoices):
    PENDING = "pending", "بانتظار"
    ACCEPTED = "accepted", "مقبول"
    WAITLIST = "waitlist", "قائمة انتظار"
    REJECTED = "rejected", "مرفوض"
    CANCELLED = "cancelled", "ملغي"
    COMPLETED = "completed", "مكتمل"


class EnrollmentSource(models.TextChoices):
    INDIVIDUAL_SELF = "individual_self", "تسجيل فردي"
    ORG_REQUEST = "org_request", "طلب جهة"


class Enrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments", verbose_name="الدورة")
    individual = models.ForeignKey("individuals.Individual", on_delete=models.CASCADE, related_name="enrollments", verbose_name="الفرد")

    source = models.CharField(
        max_length=30,
        choices=EnrollmentSource.choices,
        default=EnrollmentSource.INDIVIDUAL_SELF,
        verbose_name="مصدر التسجيل",
    )
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.PENDING,
        db_index=True,
        verbose_name="حالة التسجيل",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "تسجيل دورة"
        verbose_name_plural = "تسجيلات الدورات"
        constraints = [
            models.UniqueConstraint(fields=["course", "individual"], name="unique_enrollment_course_individual")
        ]
        indexes = [
            models.Index(fields=["course", "status"]),
            models.Index(fields=["individual", "status"]),
        ]

    def __str__(self):
        return f"{self.individual} -> {self.course.title} ({self.status})"


class OrgCourseRequestStatus(models.TextChoices):
    NEW = "new", "جديد"
    PROCESSED = "processed", "تمت المعالجة"
    CANCELLED = "cancelled", "ملغي"


class OrgCourseRequest(models.Model):
    org_branch = models.ForeignKey(
        "organizations.OrganizationBranch",
        on_delete=models.CASCADE,
        related_name="course_requests",
        verbose_name="فرع الجهة",
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="org_requests", verbose_name="الدورة")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="org_course_requests",
        verbose_name="مطلوب بواسطة",
    )

    status = models.CharField(
        max_length=20,
        choices=OrgCourseRequestStatus.choices,
        default=OrgCourseRequestStatus.NEW,
        verbose_name="حالة الطلب",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "طلب جهة لدورة"
        verbose_name_plural = "طلبات الجهات للدورات"
        indexes = [models.Index(fields=["org_branch", "course", "status"])]

    def __str__(self):
        return f"طلب {self.org_branch} -> {self.course.title}"


class OrgCourseRequestItem(models.Model):
    request = models.ForeignKey(OrgCourseRequest, on_delete=models.CASCADE, related_name="items", verbose_name="الطلب")
    individual = models.ForeignKey("individuals.Individual", on_delete=models.CASCADE, related_name="org_request_items", verbose_name="الفرد")
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="org_request_item",
        verbose_name="التسجيل الناتج (اختياري)",
    )

    class Meta:
        verbose_name = "عنصر طلب جهة"
        verbose_name_plural = "عناصر طلبات الجهات"
        constraints = [
            models.UniqueConstraint(fields=["request", "individual"], name="unique_request_item_individual")
        ]

    def __str__(self):
        return f"{self.individual} ضمن {self.request}"
