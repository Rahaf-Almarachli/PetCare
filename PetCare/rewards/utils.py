from .models import UserPointsLog
from django.db import transaction

def award_points(user, points, description):
    """
    دالة آمنة لمنح النقاط للمستخدم وتسجيلها في السجل.
    تُستخدم هذه الدالة لعمليات الكسب (EARN).
    
    Args:
        user (User): كائن المستخدم الذي سيكسب النقاط.
        points (int): عدد النقاط الموجب المراد منحه.
        description (str): وصف النشاط الذي كسب بسببه النقاط.
    
    Returns:
        int: رصيد النقاط الإجمالي الجديد للمستخدم.
    """
    if points <= 0:
        # إذا لم يكن هناك نقاط لمنحها، نعود بالرصيد الحالي
        return user.userwallet.total_points 
        
    with transaction.atomic():
        UserPointsLog.objects.create(
            user=user,
            points_change=points,
            transaction_type='EARN',
            description=description
        )
        # نعود بالرصيد الجديد المحسوب تلقائياً
        return user.userwallet.total_points