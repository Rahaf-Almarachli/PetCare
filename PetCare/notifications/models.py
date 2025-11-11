from django.db import models
from account.models import User # افتراض مسار موديل المستخدم

class PushToken(models.Model):
    """
    تخزين رموز الجهاز المستخدمة لإرسال الإشعارات الفورية عبر Pushy.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='push_tokens',
        verbose_name='المستخدم'
    )
    token = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name='رمز الجهاز (Pushy Token)'
    )
    platform = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name='المنصة'
    ) # مثال: 'android', 'ios'
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'رمز إشعار Pushy'
        verbose_name_plural = 'رموز إشعارات Pushy'
        
    def __str__(self):
        return f"{self.user.full_name or self.user.email} - {self.platform}"