from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model() # جلب نموذج المستخدم المخصص

# ====================
# 1. المكافآت الثابتة
# ====================
class Reward(models.Model):
    """ يحدد المكافآت المتاحة للتطبيق وتكلفتها النقطية. """
    name = models.CharField(max_length=100)
    points_required = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.points_required} Pts)"
        
# ====================
# 2. محفظة النقاط (الرصيد الحالي)
# ====================
class UserPoints(models.Model):
    """ يخزن إجمالي نقاط المستخدم الحالي. """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='points_wallet')
    total_points = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Points for {self.user.email}: {self.total_points}"

# ====================
# 3. سجل المعاملات (كسب واستبدال)
# ====================
class PointTransaction(models.Model):
    """ يسجل كل حركة نقطية (إيجابية أو سلبية). """
    TRANSACTION_TYPES = (
        ('EARN', 'Earned Points'),
        ('REDEEM', 'Redeemed Points'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_transactions')
    points_change = models.IntegerField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} | {self.transaction_type}: {self.points_change}"
