from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from accounts.models import UserRole


def home_view(request: HttpRequest) -> HttpResponse:
    """الصفحة الرئيسية.

    - إذا كان المستخدم "فرد" نحوله مباشرة للوحة الأفراد.
    - (لاحقًا) إذا كان "جهة" نحوله للوحة الجهات.
    """
    if request.user.is_authenticated:
        role = getattr(request.user, "role", None)
        if role == UserRole.INDIVIDUAL:
            return redirect("individuals:dashboard")

    return render(request, "home.html")
