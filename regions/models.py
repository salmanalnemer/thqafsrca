from __future__ import annotations

from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=120, unique=True, verbose_name="اسم المنطقة")
    code = models.CharField(max_length=20, unique=True, db_index=True, verbose_name="رمز المنطقة")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ آخر تحديث")

    class Meta:
        verbose_name = "منطقة"
        verbose_name_plural = "المناطق"
        ordering = ["name"]

    def __str__(self):
        return self.name
