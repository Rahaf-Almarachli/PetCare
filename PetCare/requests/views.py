from rest_framework import generics, status, permissions
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q 
import logging

# 🟢 استيرادات نظام النقاط 🟢
from reward_app.utils import award_points 
from activity.models import Activity 

# 🟢 الاستيراد المصحح لـ models و serializers 🟢
from .models import InteractionRequest as ServiceRequest 
from .serializers import (
    RequestCreateSerializer, 
    RequestDetailSerializer, 
    RequestFullDetailSerializer,
    RequestUpdateSerializer 
)

# --- الثوابت (مفاتيح الأنشطة الموحدة) ---
REQUEST_CREATED_KEY = 'SERVICE_REQUEST_CREATED' 
# المفاتيح الجديدة لطلبك
ADOPTION_APPROVED_KEY = 'ADOPTION_APPROVED'
MATING_APPROVED_KEY = 'MATING_APPROVED'
# ----------------------------------------
logger = logging.getLogger(__name__)

# ----------------------------------------------------
# 1. إنشاء طلب جديد (CreateInteractionRequestView)
# ----------------------------------------------------
class CreateInteractionRequestView(generics.CreateAPIView): 
    """ إنشاء طلب جديد (POST). """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestCreateSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request_instance = serializer.save() 
        
        points_awarded = 0
        current_points = 0
        
        # منح نقاط إنشاء الطلب (اختياري، يمكنك حذف هذا الجزء إذا كنت لا تريد منح نقاط عند الإنشاء)
        try:
            success, points_awarded = award_points(
                user=request.user, 
                activity_system_name=REQUEST_CREATED_KEY,
                description=f"Interaction request created: {request_instance.id}"
            )
            
            if success:
                current_points = getattr(request.user, 'userwallet', None).total_points if hasattr(request.user, 'userwallet') else 0

        except Exception as e:
            logger.error(f"Failed to award points for creating request to {request.user.email}: {e}")

        
        headers = self.get_success_headers(serializer.data)
        
        return Response({
            "message": "Interaction request created successfully.",
            "request_id": request_instance.id,
            "current_points": current_points,
            "points_awarded_now": points_awarded 
        }, status=status.HTTP_201_CREATED, headers=headers)


# ----------------------------------------------------
# 2. قائمة الطلبات (RequestInboxListView)
# ----------------------------------------------------
class RequestInboxListView(generics.ListAPIView): 
    """ سرد طلبات المستخدمين (GET). """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestDetailSerializer 

    def get_queryset(self):
        user = self.request.user
        return ServiceRequest.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('-created_at')

# ----------------------------------------------------
# 3. تفاصيل الطلب (RequestDetailView - أصبح Retrieve فقط)
# ----------------------------------------------------
class RequestDetailView(generics.RetrieveAPIView): 
    """ عرض التفاصيل الكاملة لطلب واحد. """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestFullDetailSerializer 
        
    def get_queryset(self):
        user = self.request.user
        return ServiceRequest.objects.filter(Q(sender=user) | Q(receiver=user))

# ----------------------------------------------------
# 4. تحديث حالة الطلب (RequestUpdateStatusView)
# ----------------------------------------------------
class RequestUpdateStatusView(generics.UpdateAPIView): 
    """ تحديث حالة الطلب (PUT/PATCH). """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestUpdateSerializer
    
    def get_queryset(self):
        user = self.request.user
        return ServiceRequest.objects.filter(Q(sender=user) | Q(receiver=user))

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        
        # 🟢 حفظ الحالة السابقة للطلب قبل التحديث 🟢
        old_status = instance.status

        # التحقق من الأذونات: فقط المُستقبِل (مالك الحيوان) يمكنه تحديث الحالة.
        if instance.receiver != user:
            return Response({"detail": "You do not have permission to modify this request's status."}, 
                            status=status.HTTP_403_FORBIDDEN)
            
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # 🟢 بعد التحديث، قم بإعادة تحميل الكائن للحصول على الحالة الجديدة 🟢
        instance.refresh_from_db()
        new_status = instance.status
        
        # 🟢 🛑 منطق منح النقاط عند القبول 🛑 🟢
        points_awarded = 0
        current_points = 0
        
        # نمنح النقاط فقط إذا كانت الحالة الجديدة هي 'Accepted' والحالة القديمة لم تكن 'Accepted'
        if new_status == 'Accepted' and old_status != 'Accepted':
            
            # تحديد مفتاح النشاط بناءً على نوع الطلب
            if instance.request_type == 'Adoption':
                activity_key = ADOPTION_APPROVED_KEY
                description = f"Adoption request accepted for pet {instance.pet.pet_name}."
            elif instance.request_type == 'Mate':
                activity_key = MATING_APPROVED_KEY
                description = f"Mating request accepted for pet {instance.pet.pet_name}."
            else:
                activity_key = None # لا تمنح نقاط إذا كان نوع الطلب غير معروف

            if activity_key:
                try:
                    # نمنح النقاط للمرسِل (الشخص الذي تم قبول طلبه)
                    success, points_awarded = award_points(
                        user=instance.sender, 
                        activity_system_name=activity_key,
                        description=description
                    )
                    
                    if success:
                        # استرجاع رصيد النقاط بعد المنح
                        user_wallet = getattr(instance.sender, 'userwallet', None)
                        current_points = user_wallet.total_points if user_wallet else 0
                        logger.info(f"Awarded {points_awarded} pts to {instance.sender.email} for request acceptance.")

                except Exception as e:
                    logger.error(f"Error awarding points for request acceptance to {instance.sender.email}: {e}")


        # 3. إرجاع الرد
        response_data = {
            "message": "Interaction request status updated successfully.",
            "request": serializer.data
        }
        
        # إضافة تفاصيل النقاط إلى الرد إذا تم منحها
        if points_awarded > 0:
            response_data['points_awarded_to_sender'] = points_awarded
            response_data['sender_current_points'] = current_points
            
        return Response(response_data, status=status.HTTP_200_OK)