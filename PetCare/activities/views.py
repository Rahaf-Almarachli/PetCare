from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Activity, ActivityLog
from .serializers import ActivitySerializer, ActivityLogSerializer, SystemActivitySerializer
# 💥 استيراد دالة منح النقاط 💥
from rewards.utils import award_points 
from django.db.utils import IntegrityError 

class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """ واجهة لعرض قائمة الأنشطة التي تكسب نقاطاً وسجل الإكمال. """
    queryset = Activity.objects.all().order_by('points_value')
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def my_logs(self, request):
        """ عرض سجل الأنشطة المكتملة للمستخدم الحالي. """
        logs = ActivityLog.objects.filter(user=request.user).order_by('-completion_time')
        serializer = ActivityLogSerializer(logs, many=True)
        return Response(serializer.data)

class SystemTriggerViewSet(viewsets.ViewSet):
    """
    نقطة نهاية (Endpoint) لاستخدامها بواسطة النظام (أو تطبيقات أخرى)
    لتسجيل إكمال نشاط ومنح النقاط.
    """
    # يمكن أن تحتاج إلى مستوى أمان مختلف هنا (مثل Token خاص بالنظام الداخلي)
    permission_classes = [permissions.IsAuthenticated] 

    @action(detail=False, methods=['post'], url_path='complete')
    def complete_system_activity(self, request):
        serializer = SystemActivitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        system_name = serializer.validated_data['system_name']
        user = request.user

        try:
            with transaction.atomic():
                # 1. جلب بيانات النشاط وقيمته
                activity = get_object_or_404(Activity, system_name=system_name)
                
                # 2. تسجيل الإكمال (سيتم الفشل هنا إذا كان النشاط قد تم إكماله مسبقًا)
                ActivityLog.objects.create(user=user, activity=activity)

                # 3. منح النقاط
                new_total_points = award_points(
                    user=user,
                    points=activity.points_value,
                    description=f'Task: {activity.name}'
                )

                return Response({
                    'detail': f'Activity "{activity.name}" completed, points awarded.',
                    'points_awarded': activity.points_value,
                    'new_total_points': new_total_points
                }, status=status.HTTP_201_CREATED)
        
        except IntegrityError:
            # يحدث هذا عند محاولة إكمال نشاط لمرة واحدة مرتين
            return Response({'detail': f'Activity "{activity.name}" already completed by this user.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Activity.DoesNotExist:
            return Response({'detail': 'Invalid activity system name.'},
                            status=status.HTTP_404_NOT_FOUND)