from django.contrib import admin

from .models import (
    Course,
    CourseSession,
    Enrollment,
    OrgCourseRequest,
    OrgCourseRequestItem,
)


class CourseSessionInline(admin.TabularInline):
    model = CourseSession
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "region", "delivery_mode", "start_at", "end_at", "capacity", "is_published", "is_active")
    list_filter = ("region", "delivery_mode", "is_published", "is_active")
    search_fields = ("title", "description", "region__name")
    ordering = ("-start_at",)
    inlines = [CourseSessionInline]

    autocomplete_fields = ("region", "created_by")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id", "course", "individual", "source", "status", "created_at")
    list_filter = ("status", "source", "course__region")
    search_fields = ("course__title", "individual__full_name", "individual__email")
    ordering = ("-id",)
    readonly_fields = ("created_at",)

    autocomplete_fields = ("course", "individual")


class OrgCourseRequestItemInline(admin.TabularInline):
    model = OrgCourseRequestItem
    extra = 0
    autocomplete_fields = ("individual", "enrollment")


@admin.register(OrgCourseRequest)
class OrgCourseRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "org_branch", "course", "requested_by", "status", "created_at")
    list_filter = ("status", "course__region")
    search_fields = ("org_branch__master__name", "course__title", "requested_by__email")
    ordering = ("-id",)
    readonly_fields = ("created_at",)
    inlines = [OrgCourseRequestItemInline]

    autocomplete_fields = ("org_branch", "course", "requested_by")
