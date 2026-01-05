import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User  # AUTH_USER_MODEL الفعلي عندك
from .models import TrainerProfile

logger = logging.getLogger(__name__)

def _is_trainer(user: User) -> bool:
    """
    عدّل هذا الشرط حسب نظام الأدوار عندك.
    السيناريوهات الشائعة:
    - user.role == "trainer"
    - user.user_role == UserRole.TRAINER
    - user.roles.filter(code="trainer").exists()
    """
    # 1) إذا عندك حقل اسمه role نصي:
    if hasattr(user, "role") and str(getattr(user, "role") or "").lower() == "trainer":
        return True

    # 2) إذا عندك علاقة/حقل مختلف: عدّله حسب مشروعك
    if hasattr(user, "user_role") and str(getattr(user, "user_role") or "").lower() == "trainer":
        return True

    return False

@receiver(post_save, sender=User)
def ensure_trainer_profile(sender, instance: User, created: bool, **kwargs):
    try:
        if _is_trainer(instance):
            TrainerProfile.objects.get_or_create(user=instance)
        else:
            # اختياري: إذا تغيّرت الصلاحية من مدرب لغيره، احذف ملف المدرب
            TrainerProfile.objects.filter(user=instance).delete()
    except Exception:
        logger.exception("Failed to sync TrainerProfile for user_id=%s", instance.pk)
