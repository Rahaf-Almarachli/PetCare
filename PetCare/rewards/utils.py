from .models import UserPoints, PointTransaction
from django.db import transaction

@transaction.atomic
def award_points(user, points, description):
    """
    يمنح نقاطًا للمستخدم ويضيف سجل معاملة بشكل آمن (Atomic).
    """
    if points <= 0:
        return 0
        
    user_points, created = UserPoints.objects.get_or_create(user=user)
    
    # 1. تحديث الرصيد
    user_points.total_points += points
    user_points.save()
    
    # 2. تسجيل المعاملة
    PointTransaction.objects.create(
        user=user,
        points_change=points,
        transaction_type='EARN',
        description=description
    )
    # نُرجع الرصيد الجديد المحدّث
    return user_points.total_points