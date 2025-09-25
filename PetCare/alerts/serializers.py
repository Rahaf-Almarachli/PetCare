# alerts/serializers.py
from rest_framework import serializers
from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ['id', 'name', 'time', 'is_active']

    def create(self, validated_data):
        request = self.context['request']
        alert = Alert.objects.create(
            owner=request.user,
            name=validated_data['name'],
            time=validated_data['time'],
            is_active=validated_data.get('is_active', True)
        )
        return alert
