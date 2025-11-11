from django.db import models
from account.models import User # Assuming User model path

class PushToken(models.Model):
    """
    Stores device tokens used for sending push notifications via Pushy.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='push_tokens',
        verbose_name='User'
    )
    token = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name='Pushy Device Token'
    )
    platform = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name='Platform'
    ) # Example: 'android', 'ios'
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Added unique_together constraint for better database integrity
        unique_together = ('user', 'token') 
        verbose_name = 'Pushy Notification Token'
        verbose_name_plural = 'Pushy Notification Tokens'
        
    def __str__(self):
        # Assuming User model has full_name and email fields
        return f"{self.user.full_name or self.user.email} - {self.platform}"