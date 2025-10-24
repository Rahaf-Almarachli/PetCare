from rest_framework import serializers
from .models import Reward, RedeemedReward, UserPoints, PointsTransaction

class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = ['id', 'title', 'description', 'points_required', 'is_active']


class RedeemedRewardSerializer(serializers.ModelSerializer):
    reward = RewardSerializer()

    class Meta:
        model = RedeemedReward
        fields = ['id', 'reward', 'redeemed_at']


class PointsSummarySerializer(serializers.Serializer):
    total_points = serializers.IntegerField()
    transactions = serializers.ListField()
