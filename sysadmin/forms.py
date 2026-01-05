from __future__ import annotations

from django import forms

from accounts.models import User, UserRole
from iam.models import Permission, RolePermission, UserPermission, PermissionRequest

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "role", "is_active", "region", "org_branch", "individual"]

class RolePermToggleForm(forms.Form):
    role = forms.ChoiceField(choices=UserRole.choices)
    permission_id = forms.IntegerField()
    allow = forms.BooleanField(required=False)

class UserPermToggleForm(forms.Form):
    user_id = forms.IntegerField()
    permission_id = forms.IntegerField()
    allow = forms.BooleanField(required=False)

class PermissionRequestDecisionForm(forms.Form):
    decision = forms.ChoiceField(choices=[("approve","اعتماد"),("reject","رفض")])
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows":3}))
    
    labels = {
        "first_name": "الاسم الأول",
        "last_name": "اسم العائلة",
        "email": "البريد الإلكتروني",
        "phone": "رقم الجوال",
        "role": "الدور",
        "is_active": "مفعل",
        "region": "المنطقة",
        "org_branch": "فرع الجهة",
        "individual": "ملف الفرد",
    }