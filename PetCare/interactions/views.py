from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Q 
from django.shortcuts import get_object_or_404
import logging

# 🌟 استيراد Pushy Notification 🌟
from notifications.utils import send_pushy_notification 

# استيرادات المكافآت والأنشطة
from reward_app.utils import award_points 
from activity.models import Activity 

# استيرادات الموديلات والسيريالايزر
from .models import InteractionRequest
from pets.models import Pet 
from adoption.models import AdoptionPost 
from mating.models import MatingPost 
from .serializers import (
    RequestCreateSerializer, 
    RequestDetailSerializer, 
    RequestFullDetailSerializer,
    RequestUpdateSerializer 
)

# مفاتيح نظام المكافآت
REQUEST_CREATED_KEY = 'SERVICE_REQUEST_CREATED' # لم يعد يستخدم في هذا الـ View
ADOPTION_APPROVED_KEY = 'ADOPTION_APPROVED'
MATING_APPROVED_KEY = 'MATING_APPROVED'

logger = logging.getLogger(__name__)


# ----------------------------------------------------
# 1. قائمة صندوق الوارد
# ----------------------------------------------------
class RequestInboxListView(generics.ListAPIView): 
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestDetailSerializer 

    def get_queryset(self):
        user = self.request.user
        return InteractionRequest.objects.filter(receiver=user).order_by('-created_at')


# ----------------------------------------------------
# 2. إنشاء طلب تفاعل (تم إضافة إشعار لمالك الحيوان)
# ----------------------------------------------------
class CreateInteractionRequestView(generics.CreateAPIView): 

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestCreateSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        # 🌟 serializer.save() سيقوم بإنشاء الطلب وإرسال إشعار للمالك 🌟
        request_instance = serializer.save() 
        
        # ----------------------------------------------------
        # 🌟 إضافة إشعار "طلب جديد" إلى مالك الحيوان (Receiver) 🌟
        # ----------------------------------------------------
        
        recipient_user = request_instance.receiver # مالك الحيوان الأليف
        sender_name = request_instance.sender.full_name or request_instance.sender.username
        pet_name = request_instance.pet.pet_name
        request_type = request_instance.request_type
        
        # إعداد الإشعار باللغة الإنجليزية
        title = f"New {request_type} Request!"
        body = f"You have a new {request_type} request from {sender_name} for {pet_name}. Please review."

        payload = {
            "action": "NEW_REQUEST_CREATED",
            "request_id": request_instance.id,
            "type": request_type
        }
        
        send_pushy_notification(recipient_user.id, title, body, payload)
        
        # ----------------------------------------------------
        
        # ❌ تمت إزالة جميع الأكواد المتعلقة بـ award_points من هنا
        
        response_serializer = RequestFullDetailSerializer(request_instance)
        
        response_data = {
            "message": "Interaction request created successfully.",
            "request_id": request_instance.id,
            "request_details": response_serializer.data,
            # ❌ تم حذف حقول النقاط من الـ Response هنا
            # "current_points": 0, 
            # "points_awarded_now": 0
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


# ----------------------------------------------------
# 3. عرض تفاصيل الطلب
# ----------------------------------------------------
class RequestDetailView(generics.RetrieveAPIView): 
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestFullDetailSerializer 
        
    def get_queryset(self):
        user = self.request.user
        return InteractionRequest.objects.filter(Q(sender=user) | Q(receiver=user))


# ----------------------------------------------------
# 4. تحديث حالة الطلب (إرسال إشعار ومنح النقاط عند القبول)
# ----------------------------------------------------
class RequestUpdateStatusView(APIView): 
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def patch(self, request, pk):
        request_obj = get_object_or_404(InteractionRequest, id=pk)
        user = request.user
        
        if request_obj.receiver != user:
            return Response(
                {"detail": "You do not have permission to modify this request's status."},
                status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get('status')
        owner_response_message = request.data.get('owner_response_message', None)
        
        if not new_status or new_status not in ['Accepted', 'Rejected']:
            return Response(
                {"detail": "Invalid or missing 'status' field (must be Accepted or Rejected)."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RequestUpdateSerializer(
            request_obj, 
            data={'status': new_status, 'owner_response_message': owner_response_message},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        request_obj = serializer.save()
        
        pet = request_obj.pet
        action_message = ""
        sender_id = request_obj.sender.id 

        # 🌟 تسجيل محاولة معالجة تحديث الحالة
        logger.info(f"Processing status update for Request {pk} to {new_status}. Target User ID: {sender_id}")
        # -----------------------------------------------------------------

        if new_status == 'Accepted':
            
            title = "Congratulations, Accepted!"
            body = f"The Owner of {pet.pet_name} Accepted The Request!"
            

            if request_obj.request_type == 'Adoption':
                pet.owner = request_obj.sender 
                pet.save()
                
                AdoptionPost.objects.filter(pet=pet).delete()
                action_message = "Ownership transferred, pet removed from adoption list."
                activity_key = ADOPTION_APPROVED_KEY
                
            elif request_obj.request_type == 'Mate':
                MatingPost.objects.filter(pet=pet).delete()
                action_message = "Mating request approved, MatingPost deleted."
                activity_key = MATING_APPROVED_KEY
            else:
                activity_key = None

            # 3. منح النقاط 
            if activity_key:
                try:
                    success, points_awarded = award_points(
                        user=request_obj.sender, 
                        activity_system_name=activity_key,
                        description=f"{request_obj.request_type} request accepted."
                    )
                    if success:
                        user_wallet = getattr(request_obj.sender, 'userwallet', None)
                        sender_current_points = user_wallet.total_points if user_wallet else 0
                except Exception as e:
                    logger.error(f"Error awarding points to {request_obj.sender.email}: {e}")

            # حذف الطلبات الأخرى المتعلقة بالحيوان
            InteractionRequest.objects.filter(pet=pet).delete()
            
            # 🌟 السطر التشخيصي الإضافي: نؤكد أننا على وشك الإرسال 
            logger.error(f"DIAGNOSTIC VIEW: Preparing to send ACCEPTED notification to User {sender_id}")
            # -----------------------------------------------------------------
            
            # 4. إرسال إشعار القبول عبر Pushy
            payload = {
                "action": "REQUEST_STATUS_UPDATE",
                "request_id": request_obj.id,
                "status": new_status,
                "pet_name": pet.pet_name
            }
            send_pushy_notification(sender_id, title, body, payload)
            
            return Response({
                "detail": f"Request accepted. Pet {pet.id} operation complete. {action_message}",
                "points_awarded_to_sender": points_awarded,
                "sender_current_points": sender_current_points
            }, status=status.HTTP_200_OK)
        
        elif new_status == 'Rejected':
            
            title = "Sorry, Rejected"
            body = f"The Owner of {pet.pet_name} Rejected The Request!"
            payload = {
                "action": "REQUEST_STATUS_UPDATE",
                "request_id": request_obj.id,
                "status": new_status,
                "pet_name": pet.pet_name
            }
            
            # 🌟 السطر التشخيصي الإضافي: نؤكد أننا على وشك الإرسال
            logger.error(f"DIAGNOSTIC VIEW: Preparing to send REJECTED notification to User {sender_id}")
            # -----------------------------------------------------------------
            
            # 🚨 التعديل: إرسال الإشعار أولاً
            send_pushy_notification(sender_id, title, body, payload)
            
            # 🚨 ثم حذف الطلب
            request_id = request_obj.id
            request_obj.delete()

            return Response(
                {"detail": f"Request {request_id} rejected and deleted from your inbox."},
                status=status.HTTP_200_OK
            )
        
        # -----------------------------------------------------------------
        
        else:
            return Response({"detail": "Status updated successfully."}, status=status.HTTP_200_OK)