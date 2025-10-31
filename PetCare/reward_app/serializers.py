from rest_framework import serializers
from .models import UserWallet

class UserWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWallet
        fields = ('total_points',)
        read_only_fields = fields

class RedeemRequestSerializer(serializers.Serializer):
    reward_system_name = serializers.CharField(
        max_length=50,
        help_text="The system key of the reward to redeem (e.g., FREE_GROOMING)."
    )