from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model() 

# 1. المكافآت الثابتة القابلة للاستبدال
class Reward(models.Model):
    """ يحدد المكافآت المتاحة للتطبيق وتكلفتها النقطية (مثل: Free Grooming). """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    points_required = models.IntegerField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.points_required} Pts)"
        
# 2. محفظة النقاط (الرصيد الحالي للمستخدم)
class UserPoints(models.Model):
    """ يخزن إجمالي نقاط المستخدم الحالي. """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='points_wallet')
    total_points = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Points for {self.user.username}: {self.total_points}"

# 3. سجل المعاملات
class PointTransaction(models.Model):
    """ يسجل كل حركة نقطية (إيجابية أو سلبية). """
    TRANSACTION_TYPES = (
        ('EARN', 'Earned Points'),
        ('REDEEM', 'Redeemed Points'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_transactions')
    points_change = models.IntegerField() # قيمة التغيير (موجبة للكسب، سالبة للاستبدال)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} | {self.transaction_type}: {self.points_change}"