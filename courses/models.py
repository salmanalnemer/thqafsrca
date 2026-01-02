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
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_courses",
    )

    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    delivery_mode = models.CharField(max_length=20, choices=DeliveryMode.choices, default=DeliveryMode.IN_PERSON)

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    capacity = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    allow_individuals = models.BooleanField(default=True)
    allow_organizations = models.BooleanField(default=True)

    is_published = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
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
    """
    اختياري: لو الدورة عدة أيام/جلسات.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sessions")
    title = models.CharField(max_length=200, blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    def __str__(self):
        return f"Session for {self.course.title}"


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
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    individual = models.ForeignKey("individuals.Individual", on_delete=models.CASCADE, related_name="enrollments")

    source = models.CharField(max_length=30, choices=EnrollmentSource.choices, default=EnrollmentSource.INDIVIDUAL_SELF)
    status = models.CharField(max_length=20, choices=EnrollmentStatus.choices, default=EnrollmentStatus.PENDING, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
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
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="org_requests")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="org_course_requests",
    )

    status = models.CharField(max_length=20, choices=OrgCourseRequestStatus.choices, default=OrgCourseRequestStatus.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["org_branch", "course", "status"])]

    def __str__(self):
        return f"Request {self.org_branch} -> {self.course.title}"


class OrgCourseRequestItem(models.Model):
    request = models.ForeignKey(OrgCourseRequest, on_delete=models.CASCADE, related_name="items")
    individual = models.ForeignKey("individuals.Individual", on_delete=models.CASCADE, related_name="org_request_items")
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="org_request_item",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["request", "individual"], name="unique_request_item_individual")
        ]

    def __str__(self):
        return f"{self.individual} in {self.request}"
