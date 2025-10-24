from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.db import transaction

from django.contrib.auth import get_user_model
User = get_user_model()

from rewards.models import UserPoints, PointsTransaction
# نربط الأحداث التالية بالـ models الخاصة بتطبيقاتك:
from adoption.models import AdoptionPost
from mating.models import MatingPost

# نقاط كل حدث — يمكنك تعديل القيم هنا أو عبر إعداد settings
PROFILE_COMPLETE_POINTS = getattr(settings, 'REWARD_PROFILE_COMPLETE_POINTS', 50)
ADOPTION_POST_POINTS = getattr(settings, 'REWARD_ADOPTION_POINTS', 100)
MATING_POST_POINTS = getattr(settings, 'REWARD_MATING_POINTS', 80)

def ensure_userpoints(user):
    up, _ = UserPoints.objects.get_or_create(user=user)
    return up

def award_points(user, event_type, reference, amount):
    """
    منحه نقاط مع تسجيل عملية (ويمنع تكرار نفس event+reference).
    سترجع (True, message) عند الإضافة، و(False,message) إذا تم تجاهلها.
    """
    # منع التكرار: إذا وجدنا سجل بنفس user,event_type,reference فلا نكرر
    exists = PointsTransaction.objects.filter(
        user=user, event_type=event_type, reference=str(reference)
    ).exists()
    if exists:
        return False, "Already awarded."

    with transaction.atomic():
        up = ensure_userpoints(user)
        up.balance += amount
        up.save()
        PointsTransaction.objects.create(
            user=user, event_type=event_type, reference=str(reference), amount=amount
        )
    return True, "Awarded."

@receiver(post_save, sender=AdoptionPost)
def on_adoption_post_created(sender, instance, created, **kwargs):
    if not created:
        return
    # صحة: من يجب منحه النقاط؟ صاحب الـ pet (owner)
    pet = instance.pet
    user = pet.owner
    award_points(user, 'adoption_post', reference=f"adoptionpost:{instance.id}", amount=ADOPTION_POST_POINTS)

@receiver(post_save, sender=MatingPost)
def on_mating_post_created(sender, instance, created, **kwargs):
    if not created:
        return
    pet = instance.pet
    user = pet.owner
    award_points(user, 'mating_post', reference=f"matingpost:{instance.id}", amount=MATING_POST_POINTS)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
User = get_user_model()

PROFILE_REQUIRED_FIELDS = getattr(settings, 'REWARD_PROFILE_REQUIRED_FIELDS', ['phone','location','profile_picture'])

@receiver(post_save, sender=User)
def on_user_saved_check_profile(sender, instance, created, **kwargs):
    # إذا تم الإنشاء فقط ننتظر إن يملأ الملف لاحقاً
    # لكن سنفحص كل مرة: لو الحقول المطلوبة ممتلئة ولم تُعطَ النقاط من قبل => اعطها
    try:
        # هل أعطيت مسبقًا نقطة profile_complete؟
        from rewards.models import PointsTransaction
        already = PointsTransaction.objects.filter(user=instance, event_type='profile_complete').exists()
        if already:
            return
    except Exception:
        already = False

    # التحقق من الحقول المطلوبة
    ok = True
    for f in PROFILE_REQUIRED_FIELDS:
        val = getattr(instance, f, None)
        if not val:
            ok = False
            break
    if ok:
        award_points(instance, 'profile_complete', reference='profile', amount=PROFILE_COMPLETE_POINTS)
