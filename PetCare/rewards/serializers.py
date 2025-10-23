from rest_framework import serializers
from .models import Reward, UserPoints, PointTransaction

class RewardSerializer(serializers.ModelSerializer):
    """ لتسلسل المكافآت المتاحة للاستبدال """
    class Meta:
        model = Reward
        fields = ['id', 'name', 'points_required', 'description']

class RedeemSerializer(serializers.Serializer):
    """ لطلب استبدال المكافأة: يحتاج فقط إلى معرّف المكافأة """
    reward_id = serializers.IntegerField()

class PointTransactionSerializer(serializers.ModelSerializer):
    """ لعرض سجل المعاملات """
    class Meta:
        model = PointTransaction
        fields = ['points_change', 'transaction_type', 'description', 'timestamp']