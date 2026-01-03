from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
def contact_view(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        message = request.POST.get("message", "").strip()

        if not name or not email or not message:
            messages.error(request, "فضلاً أكمل جميع الحقول.")
            return redirect("contact")

        # لاحقًا تقدر:
        # - تحفظ في DB
        # - أو ترسل بريد
        messages.success(request, "تم استلام رسالتك بنجاح، شكرًا لتواصلك.")
        return redirect("contact")

    return render(request, "contact_temp/contact.html")
