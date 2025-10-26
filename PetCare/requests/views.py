from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.db import transaction 
from django.db.utils import IntegrityError
import logging

# 🟢 الاستيرادات الجديدة لنظام النقاط 🟢
from rewards.utils import award_points
from activities.models import Activity, ActivityLog 

from .models import InteractionRequest
from pets.models import Pet 
from adoption.models import AdoptionPost 
from mating.models import MatingPost 
from .serializers import (
    RequestCreateSerializer, 
    RequestDetailSerializer, 
    RequestFullDetailSerializer 
)

logger = logging.getLogger(__name__)

# ----------------------------------------------------
# 1. View لعرض قائمة الطلبات (Inbox)
# ----------------------------------------------------
class RequestInboxListView(generics.ListAPIView):
    """
    GET: عرض جميع الطلبات الواردة للمستخدم الحالي (بصفته المالك/المستقبل).
    """
    serializer_class = RequestDetailSerializer 
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = InteractionRequest.objects.filter(
            receiver=user
        ).select_related(
            'sender', 'pet'
        ).order_by('-created_at')
        
        return queryset

# ----------------------------------------------------
# 2. View لعرض تفاصيل الطلب (Detail)
# ----------------------------------------------------
class RequestDetailView(generics.RetrieveAPIView):
    """
    GET: عرض تفاصيل طلب معين.
    """
    serializer_class = RequestFullDetailSerializer 
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        return InteractionRequest.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender', 'pet')

# ----------------------------------------------------
# 3. View لإنشاء طلب جديد
# ----------------------------------------------------
class CreateInteractionRequestView(generics.CreateAPIView):
    """
    POST: إنشاء طلب تفاعل جديد.
    """
    serializer_class = RequestCreateSerializer 
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save()
        # 💥 هنا يتم استخدام Serializer التفصيلي لعرض بيانات المرسل/المستقبل كاملاً
        response_serializer = RequestFullDetailSerializer(instance) 
        return response_serializer.data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        response_data = self.perform_create(serializer)
        
        return Response(response_data, status=status.HTTP_201_CREATED)

# ----------------------------------------------------
# 4. View لتحديث حالة الطلب (قبول/رفض)
# ----------------------------------------------------
class RequestUpdateStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def patch(self, request, id):
        request_obj = get_object_or_404(InteractionRequest, id=id)
        user = request.user

        # التحقق من أن المستخدم هو المستقبل (الموافق)
        if request_obj.receiver != user:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        pet = request_obj.pet

        if not new_status or new_status not in ['Accepted', 'Rejected']:
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        request_obj.status = new_status
        request_obj.save(update_fields=['status'])

        if new_status == 'Accepted':
            sender = request_obj.sender
            action_message = ""
            points_awarded = 0
            
            # 🟢 منطق الكسب
            try:
                # 🏆 تبنّي (200 نقطة)
                if request_obj.request_type == 'Adoption':
                    ACTIVITY_NAME = 'ADOPT_PET'
                    
                    # نقل ملكية الحيوان وحذف المنشور والطلبات الأخرى
                    pet.owner = sender
                    pet.save()
                    AdoptionPost.objects.filter(pet=pet).delete()
                    
                    # منح النقاط
                    activity = Activity.objects.get(system_name=ACTIVITY_NAME)
                    award_points(
                        user=sender,
                        points=activity.points_value,
                        description=f'Task: {activity.name} - Pet {pet.id}'
                    )
                    points_awarded = activity.points_value
                    ActivityLog.objects.create(user=sender, activity=activity)
                    
                    action_message = f"Adoption completed (+{points_awarded} points)."

                # 🏆 تزاوج (100 نقطة)
                elif request_obj.request_type == 'Mate':
                    ACTIVITY_NAME = 'PET_MATING'
                    
                    # حذف منشور التزاوج والطلبات الأخرى
                    MatingPost.objects.filter(pet=pet).delete()
                    
                    # منح النقاط
                    activity = Activity.objects.get(system_name=ACTIVITY_NAME)
                    award_points(
                        user=sender,
                        points=activity.points_value,
                        description=f'Task: {activity.name} - Pet {pet.id}'
                    )
                    points_awarded = activity.points_value
                    ActivityLog.objects.create(user=sender, activity=activity)
                    
                    action_message = f"Mating completed (+{points_awarded} points)."

            except Activity.DoesNotExist:
                logger.error(f"Activity '{ACTIVITY_NAME}' not found in database. Check initial setup.")
                action_message = "Action completed, but points were NOT awarded (Activity not found)."
            except IntegrityError:
                 logger.warning(f"User {sender.email} attempted duplicate {ACTIVITY_NAME} award (Integrity Error).")

            # حذف جميع الطلبات الأخرى المتعلقة بهذا الحيوان (لأن العملية انتهت)
            InteractionRequest.objects.filter(pet=pet).delete()

            # استرجاع رصيد النقاط الجديد للمرسل (الكاسب)
            current_points = sender.userwallet.total_points

            return Response(
                {
                    "detail": f"Request accepted. {action_message}",
                    "new_total_points": current_points,
                    "points_awarded": points_awarded
                },
                status=status.HTTP_200_OK
            )

        elif new_status == 'Rejected':
            # نرفض الطلب ونحذفه
            request_obj.delete()
            return Response({"detail": "Request rejected."}, status=status.HTTP_200_OK)