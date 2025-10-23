from rest_framework import serializers
from .models import Activity, ActivityLog

class ActivitySerializer(serializers.ModelSerializer):
    """ لعرض قائمة الأنشطة التي تمنح نقاطاً. """
    class Meta:
        model = Activity
        fields = ['id', 'name', 'points_value', 'system_name']

class ActivityLogSerializer(serializers.ModelSerializer):
    activity_name = serializers.CharField(source='activity.name', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = ['activity_name', 'completion_time']

class SystemActivitySerializer(serializers.Serializer):
    """ يستخدم لنقاط النهاية التي يرسل لها النظام لإنهاء مهمة """
    system_name = serializers.CharField(max_length=50)