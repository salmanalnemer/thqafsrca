# thqaf/urls.py
from django.contrib import admin
from django.urls import path, include
from .views import home_view

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # صفحة الهبوط (الرئيسية) - الأفضل تكون home.html وليس base.html
    path("", home_view, name="home"),
    path("admin/", admin.site.urls),

    path("accounts/", include("accounts.urls")),
    path("regions/", include("regions.urls")),
    path("organizations/", include("organizations.urls")),
    path("individuals/", include("individuals.urls")),
    path("courses/", include("courses.urls")),
    path("attendance/", include("attendance.urls")),
    path("certificates/", include("certificates.urls")),
    path("support/", include("support.urls")),
    path("contact/", include("contact.urls")),
    path("staff/", include("staff.urls")),
    path("sansadmin/", include("sysadmin.urls")), # لوحة تحكم مدير النظام بإسم خاص 
    path("trainers/", include("trainers.urls")), 
]

# ✅ تفعيل خدمة ملفات static/media أثناء التطوير فقط (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
