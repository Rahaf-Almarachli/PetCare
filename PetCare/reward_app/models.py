from django.db import models
from django.conf import settings
import uuid
# 🛑 تم التعديل: استيراد نموذج Activity من تطبيق activity
from activity.models import Activity 

User = settings.AUTH_USER_MODEL 

# ----------------------------------------------------
# 1. UserWallet (محفظة المستخدم)
# ----------------------------------------------------
class UserWallet(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='userwallet', 
        verbose_name="User"
    )
    total_points = models.IntegerField(default=0, verbose_name="Total Points Balance") 
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet for {self.user.email}: {self.total_points} pts"

    class Meta:
        verbose_name = "User Wallet"
        verbose_name_plural = "User Wallets"
        
# ----------------------------------------------------
# 2. RedeemLog (سجل استبدال النقاط)
# ----------------------------------------------------
class RedeemLog(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending fulfillment'),
        ('FULFILLED', 'Fulfilled'),
        ('CANCELLED', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='redeem_logs')
    reward = models.ForeignKey(Activity, on_delete=models.SET_NULL, null=True)
    points_deducted = models.IntegerField(verbose_name="Points Deducted")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} redeemed {self.points_deducted} pts for {self.reward.name if self.reward else 'Unknown'}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Points Redeem Log"
        verbose_name_plural = "Points Redeem Logs"

# ----------------------------------------------------
# 3. RewardCoupon (كوبونات الجوائز)
# ----------------------------------------------------
class RewardCoupon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupons')
    reward = models.ForeignKey(Activity, on_delete=models.CASCADE)
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) 
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Coupon for {self.reward.name} - {self.code}"