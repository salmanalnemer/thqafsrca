"""
URL configuration for thqaf project.

The `urlpatterns` list routes URLs to views. For more information please see:
https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Platform apps (8)
    path('accounts/', include('accounts.urls')),            # الهوية/الدخول/OTP
    path('regions/', include('regions.urls')),              # المناطق
    path('organizations/', include('organizations.urls')),  # الجهات + تسجيل الجهات
    path('individuals/', include('individuals.urls')),      # الأفراد + تسجيل الأفراد
    path('courses/', include('courses.urls')),              # الدورات
    path('attendance/', include('attendance.urls')),        # تأكيد الحضور
    path('certificates/', include('certificates.urls')),    # الشهادات + التحقق
    path('support/', include('support.urls')),              # الدعم الفني
]
