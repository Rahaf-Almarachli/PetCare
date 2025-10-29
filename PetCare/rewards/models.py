from django.db import models
from django.conf import settings
from django.db.models import Sum

# -----------------
# 1. نموذج المكافآت (Reward)
# -----------------
class Reward(models.Model):
    name = models.CharField(max_length=100, unique=True)
    points_required = models.PositiveIntegerField()
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.points_required} pts)"

# -----------------
# 2. نموذج سجل النقاط (UserPointsLog)
# -----------------
class UserPointsLog(models.Model):
    TRANSACTION_TYPES = [
        ('EARN', 'Earned Points'),
        ('REDEEM', 'Redeemed Points'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='points_logs')
    points_change = models.IntegerField(
        help_text="Positive for earning, negative for redeeming/deduction."
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "User Points Log"
        verbose_name_plural = "User Points Logs"

    def __str__(self):
        return f"{self.user.email} | {self.points_change} pts ({self.transaction_type})"

# -----------------
# 3. نموذج المحفظة الوهمي (UserWallet) والمدير المخصص
# -----------------
class UserWalletManager(models.Manager):
    def get_user_total_points(self, user):
        """ يحسب مجموع النقاط للمستخدم من سجل المعاملات. """
        result = UserPointsLog.objects.filter(user=user).aggregate(Sum('points_change'))
        return result['points_change__sum'] or 0

class UserWallet(models.Model):
    """ نموذج وهمي لإدارة المحفظة. """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    
    objects = UserWalletManager()

    @property
    def total_points(self):
        """ خاصية تُعيد الرصيد المحسوب. """
        # التعديل الحاسم: استخدام UserWallet.objects بدلاً من self.objects
        return UserWallet.objects.get_user_total_points(self.user) 
    
    def __str__(self):
        return f"Wallet for {self.user.email} | Total Points: {self.total_points}"