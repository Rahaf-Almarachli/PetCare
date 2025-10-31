from django.contrib import admin
from .models import UserWallet, RedeemLog, RewardCoupon

@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_points', 'last_updated')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('user', 'total_points', 'last_updated') 
    list_filter = ('total_points',)

@admin.register(RedeemLog)
class RedeemLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'reward', 'points_deducted', 'status', 'created_at')
    list_filter = ('status', 'reward')
    search_fields = ('user__email', 'reward__name')
    readonly_fields = ('user', 'reward', 'points_deducted', 'created_at')

@admin.register(RewardCoupon)
class RewardCouponAdmin(admin.ModelAdmin):
    list_display = ('user', 'reward', 'code', 'is_used', 'created_at')
    list_filter = ('is_used', 'reward')
    search_fields = ('user__email', 'code')
    readonly_fields = ('user', 'reward', 'code', 'created_at')