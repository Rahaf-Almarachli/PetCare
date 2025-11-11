from rest_framework import serializers
from .models import PushToken

class PushTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushToken
        fields = ['token', 'platform'] 
        
    def create(self, validated_data):
        user = self.context['request'].user
        token = validated_data['token']
        platform = validated_data.get('platform')
        
        # تحديث الـ Token إذا كان موجوداً، وإلا يتم إنشاء كائن جديد
        push_token, created = PushToken.objects.update_or_create(
            user=user,
            token=token,
            defaults={'platform': platform}
        )
        return push_token