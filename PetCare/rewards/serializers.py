from rest_framework import serializers
from .models import Reward, UserPoints, PointTransaction
from pets.models import Pet # نحتاجها للتحقق من الأنشطة المكتملة

class RewardSerializer(serializers.ModelSerializer):
    """ لتسلسل المكافآت المتاحة للاستبدال """
    class Meta:
        model = Reward
        fields = ['id', 'name', 'points_required',]

class RedeemSerializer(serializers.Serializer):
    """ لطلب استبدال المكافأة """
    reward_id = serializers.IntegerField()

class PointTransactionSerializer(serializers.ModelSerializer):
    """ لعرض سجل المعاملات """
    class Meta:
        model = PointTransaction
        fields = ['points_change', 'transaction_type', 'description', 'timestamp']