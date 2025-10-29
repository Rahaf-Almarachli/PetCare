from rest_framework import serializers
from .models import UserWallet, Reward, UserPointsLog

## ----------------------------------------------------
## 1. Serializer لعرض محفظة المستخدم (الرصيد الكلي)
## ----------------------------------------------------

class UserWalletSerializer(serializers.ModelSerializer):
    # نستخدم ReadOnlyField لعرض البريد الإلكتروني للمستخدم بدلاً من ID
    user_email = serializers.ReadOnlyField(source='user.email')
    
    # الحل النهائي: استخدام SerializerMethodField لضمان قراءة الخاصية المحسوبة
    total_points = serializers.SerializerMethodField() 
    
    class Meta:
        model = UserWallet
        fields = ['user_email', 'total_points']

    # الدالة الخاصة بـ SerializerMethodField
    # تقوم باستدعاء خاصية total_points المحسوبة في نموذج UserWallet مباشرة (obj.total_points)
    def get_total_points(self, obj):
        # obj هو مثيل (instance) UserWallet الحالي
        return obj.total_points
        
## ----------------------------------------------------
## 2. Serializer لعرض سجل المعاملات (Logs)
## ----------------------------------------------------

class UserPointsLogSerializer(serializers.ModelSerializer):
    # لعرض نوع العملية بشكل مقروء (مثلاً: Earned Points بدلاً من EARN)
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display', 
        read_only=True
    )
    
    class Meta:
        model = UserPointsLog
        fields = [
            'id', 
            'points_change', 
            'transaction_type_display', 
            'description', 
            'timestamp'
        ]

## ----------------------------------------------------
## 3. Serializer لعرض المكافآت المتاحة للاستبدال
## ----------------------------------------------------

class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = [
            'id', 
            'name', 
            'points_required', 
            'description', 
            'is_active'
        ]