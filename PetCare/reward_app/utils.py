from django.db import transaction
from django.shortcuts import get_object_or_404
import logging
# 🛑 تم التعديل: استيراد من تطبيق activity
from activity.models import Activity, ActivityLog
from .models import UserWallet, RedeemLog

logger = logging.getLogger(__name__)

# ----------------------------------------------------
# 1. دالة منح النقاط (award_points) - مُعَدَّلة
# ----------------------------------------------------
def award_points(user, activity_system_name: str, description: str = None):
    """
    يمنح نقاطًا للمستخدم بناءً على مفتاح النشاط، ويتحقق من الأنشطة المخصصة لمرة واحدة.
    """
    try:
        activity = Activity.objects.get(system_name=activity_system_name)
    except Activity.DoesNotExist:
        logger.error(f"Activity with system_name '{activity_system_name}' not found.")
        # 🟢 نُعيد هنا False والقيمة 0 كنقاط
        return False, 0
    
    if activity.interaction_type != 'EARN':
        logger.warning(f"Attempted to award points for a REDEEM activity: {activity_system_name}")
        return False, 0

    # 🛑 منطق التحقق من الأنشطة لمرة واحدة فقط (is_once_only) 🛑
    if activity.is_once_only:
        if ActivityLog.objects.filter(user=user, activity=activity).exists():
            logger.warning(f"User {user.email} already completed once-only activity: {activity_system_name}.")
            return False, 0 # لا نمنح النقاط إذا تم إنجازها بالفعل

    points_to_award = activity.points_value
    
    with transaction.atomic():
        # 1. إنشاء سجل النشاط (ActivityLog)
        ActivityLog.objects.create(
            user=user,
            activity=activity,
            points_awarded=points_to_award,
            description=description
        )
        
        # 2. تحديث المحفظة (UserWallet)
        # نستخدم get_or_create لضمان وجود المحفظة دائمًا
        wallet, created = UserWallet.objects.get_or_create(user=user)
        wallet.total_points += points_to_award
        wallet.save()
        
    logger.info(f"User {user.email} awarded {points_to_award} pts for {activity_system_name}.")
    # 🟢 نُعيد True وقيمة النقاط الممنوحة
    return True, points_to_award

# ----------------------------------------------------
# 2. دالة استبدال النقاط (redeem_points)
# ----------------------------------------------------
def redeem_points(user, reward_system_name: str, details: dict = None):
    """
    يخصم النقاط من المستخدم ويُنشئ سجل استبدال. (كما هي)
    """
    try:
        reward = Activity.objects.get(system_name=reward_system_name)
    except Activity.DoesNotExist:
        return {'success': False, 'message': "Reward not found."}
    
    if reward.interaction_type != 'REDEEM':
        return {'success': False, 'message': "Activity is not a redeemable reward."}
    
    points_cost = reward.points_value 
    
    try:
        with transaction.atomic():
            # تأمين الصف لمنع شروط السباق (Race Conditions)
            wallet = UserWallet.objects.select_for_update().get(user=user)
            
            if wallet.total_points < points_cost:
                return {'success': False, 'message': "Insufficient points balance."}
                
            wallet.total_points -= points_cost
            wallet.save()
            
            RedeemLog.objects.create(
                user=user,
                reward=reward,
                points_deducted=points_cost,
                details=details
            )

        logger.info(f"User {user.email} redeemed {points_cost} pts for {reward_system_name}.")
        return {
            'success': True, 
            'message': f"Successfully redeemed {points_cost} points for {reward.name}.",
            'new_balance': wallet.total_points,
            'reward_object': reward 
        }
        
    except UserWallet.DoesNotExist:
        return {'success': False, 'message': "User wallet not found."}