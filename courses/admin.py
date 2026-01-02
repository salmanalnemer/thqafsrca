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
    verbose_name = "جلسة"
    verbose_name_plural = "جلسات الدورة"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "region", "delivery_mode", "start_at", "end_at", "capacity", "is_published", "is_active")
    list_display_links = ("id", "title")
    list_filter = ("region", "delivery_mode", "is_published", "is_active")
    search_fields = ("title", "description", "region__name")
    ordering = ("-start_at",)

    inlines = [CourseSessionInline]
    autocomplete_fields = ("region", "created_by")

    fieldsets = (
        ("بيانات الدورة", {"fields": ("title", "description", "region", "delivery_mode")}),
        ("الجدولة", {"fields": ("start_at", "end_at")}),
        ("الإعدادات", {"fields": ("capacity", "allow_individuals", "allow_organizations")}),
        ("النشر والحالة", {"fields": ("is_published", "is_active")}),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id", "course", "individual", "source", "status", "created_at")
    list_display_links = ("id", "course")
    list_filter = ("status", "source", "course__region")
    search_fields = ("course__title", "individual__full_name", "individual__email")
    ordering = ("-id",)
    readonly_fields = ("created_at",)

    autocomplete_fields = ("course", "individual")

    fieldsets = (
        ("بيانات التسجيل", {"fields": ("course", "individual", "source", "status")}),
        ("معلومات النظام", {"fields": ("created_at",)}),
    )


class OrgCourseRequestItemInline(admin.TabularInline):
    model = OrgCourseRequestItem
    extra = 0
    autocomplete_fields = ("individual", "enrollment")
    verbose_name = "موظف/فرد مختار"
    verbose_name_plural = "الموظفون/الأفراد المختارون"


@admin.register(OrgCourseRequest)
class OrgCourseRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "org_branch", "course", "requested_by", "status", "created_at")
    list_display_links = ("id", "org_branch")
    list_filter = ("status", "course__region")
    search_fields = ("org_branch__master__name", "course__title", "requested_by__email")
    ordering = ("-id",)
    readonly_fields = ("created_at",)

    inlines = [OrgCourseRequestItemInline]
    autocomplete_fields = ("org_branch", "course", "requested_by")

    fieldsets = (
        ("بيانات الطلب", {"fields": ("org_branch", "course", "requested_by", "status")}),
        ("معلومات النظام", {"fields": ("created_at",)}),
    )
