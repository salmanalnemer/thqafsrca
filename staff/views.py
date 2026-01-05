# staff/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from staff.decorators import staff_required


def _ctx(request, active: str) -> dict:
    return {
        "active": active,
        "display_name": (request.session.get("display_name") or "").strip(),  # ✅ الاسم فقط
        "region": (request.session.get("region") or "").strip(),              # ✅ المنطقة
    }


@login_required
@staff_required
def dashboard(request):
    return render(request, "staff/dashboard.html", _ctx(request, "dashboard"))


@login_required
@staff_required
def course_open(request):
    return render(request, "staff/courses/open_course.html", _ctx(request, "course_open"))


@login_required
@staff_required
def course_approve(request):
    return render(request, "staff/courses/approve_courses.html", _ctx(request, "course_approve"))


@login_required
@staff_required
def courses_opened(request):
    return render(request, "staff/courses/opened_courses.html", _ctx(request, "courses_opened"))


@login_required
@staff_required
def courses_closed(request):
    return render(request, "staff/courses/closed_courses.html", _ctx(request, "courses_closed"))


@login_required
@staff_required
def courses_mine(request):
    return render(request, "staff/courses/my_courses.html", _ctx(request, "courses_mine"))
