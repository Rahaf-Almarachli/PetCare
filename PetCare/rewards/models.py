from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserPoints(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='points')
    balance = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.email} - {self.balance} pts"


class PointsTransaction(models.Model):
    EVENT_CHOICES = [
        ('profile_completed', 'Profile Completed'),
        ('adoption_success', 'Adoption Success'),
        ('mating_success', 'Mating Success'),
        ('reward_redeemed', 'Reward Redeemed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    reference = models.CharField(max_length=200, blank=True, null=True)
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sign = "+" if self.amount > 0 else ""
        return f"{self.user.email} - {self.event_type} ({sign}{self.amount})"


# 🏆 قائمة المكافآت المتاحة
class Reward(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    points_required = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.points_required} pts)"


# 💎 سجل المكافآت التي استبدلها المستخدم
class RedeemedReward(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='redeemed_rewards')
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE, related_name='redemptions')
    redeemed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} redeemed {self.reward.title}"
