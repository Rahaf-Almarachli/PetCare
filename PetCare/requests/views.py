from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Q 
from django.shortcuts import get_object_or_404
import logging

# 🟢 استيرادات نظام النقاط 🟢
from reward_app.utils import award_points 
from activity.models import Activity # (قد لا تحتاج إليها إذا كانت فقط award_points كافية)

# 🟢 استيرادات النماذج والمسلسلات 🟢
from .models import InteractionRequest
from pets.models import Pet 
from adoption.models import AdoptionPost 
from mating.models import MatingPost 
from .serializers import (
    RequestCreateSerializer, 
    RequestDetailSerializer, 
    RequestFullDetailSerializer,
    RequestUpdateSerializer # (سنستخدمه بشكل غير مباشر في APIView)
)

# --- الثوابت (مفاتيح الأنشطة الموحدة) ---
REQUEST_CREATED_KEY = 'SERVICE_REQUEST_CREATED' 
ADOPTION_APPROVED_KEY = 'ADOPTION_APPROVED'
MATING_APPROVED_KEY = 'MATING_APPROVED'
# ----------------------------------------
logger = logging.getLogger(__name__)

# ----------------------------------------------------
# 1. قائمة الطلبات الواردة فقط (RequestInboxListView)
# ----------------------------------------------------
class RequestInboxListView(generics.ListAPIView): 
    """ 
    سرد الطلبات المرسلة إلى المستخدم الحالي (حيث يكون المستخدم هو receiver حصراً).
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestDetailSerializer 

    def get_queryset(self):
        user = self.request.user
        # 🟢 التصحيح: فقط الطلبات التي يكون فيها المستخدم هو المُستقبِل (receiver)
        return InteractionRequest.objects.filter(receiver=user).order_by('-created_at')

# ----------------------------------------------------
# 2. إنشاء طلب جديد (CreateInteractionRequestView)
# ----------------------------------------------------
class CreateInteractionRequestView(generics.CreateAPIView): 
    """ إنشاء طلب جديد (POST) مع منح نقاط عند الإنشاء. """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestCreateSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request_instance = serializer.save() 
        
        points_awarded = 0
        current_points = 0
        
        # منح نقاط إنشاء الطلب
        try:
            success, points_awarded = award_points(
                user=request.user, 
                activity_system_name=REQUEST_CREATED_KEY,
                description=f"Interaction request created: {request_instance.id}"
            )
            
            if success:
                user_wallet = getattr(request.user, 'userwallet', None)
                current_points = user_wallet.total_points if user_wallet else 0
        except Exception as e:
            logger.error(f"Failed to award points for creating request: {e}")

        # استخدام RequestFullDetailSerializer لعرض الرد المنقّى والمفصل (كما اتفقنا سابقاً)
        response_serializer = RequestFullDetailSerializer(request_instance)
        
        response_data = {
            "message": "Interaction request created successfully.",
            "request_id": request_instance.id,
            "request_details": response_serializer.data, # إرجاع التفاصيل المطلوبة
            "current_points": current_points,
            "points_awarded_now": points_awarded 
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


# ----------------------------------------------------
# 3. تفاصيل الطلب (RequestDetailView)
# ----------------------------------------------------
class RequestDetailView(generics.RetrieveAPIView): 
    """ عرض التفاصيل الكاملة لطلب واحد. """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestFullDetailSerializer 
        
    def get_queryset(self):
        user = self.request.user
        # يمكن للمستخدم رؤية الطلب إذا كان مُرسِلاً (sender) أو مُستقبِلاً (receiver)
        return InteractionRequest.objects.filter(Q(sender=user) | Q(receiver=user))

# ----------------------------------------------------
# 4. تحديث حالة الطلب (RequestUpdateStatusView)
# ----------------------------------------------------
class RequestUpdateStatusView(APIView): 
    """ 
    تحديث حالة الطلب (قبول/رفض) مع منطق نقل الملكية ومنح النقاط.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def patch(self, request, pk):
        request_obj = get_object_or_404(InteractionRequest, id=pk)
        user = request.user
        
        # 1. التحقق من الصلاحيات: فقط المُستقبِل (مالك الحيوان) يمكنه تحديث الحالة.
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
        
        # 2. تحديث الحالة ورسالة الرد
        # 🟢 نستخدم RequestUpdateSerializer للتحقق من صحة البيانات (اختياري لكن أفضل)
        serializer = RequestUpdateSerializer(
            request_obj, 
            data={'status': new_status, 'owner_response_message': owner_response_message},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save() 
        
        pet = request_obj.pet
        action_message = ""
        
        # 3. منطق القبول (Accepted)
        if new_status == 'Accepted':
            
            # 🟢 منطق منح النقاط للمرسِل (الذي تم قبول طلبه) 🟢
            points_awarded = 0
            sender_current_points = 0
            
            if request_obj.request_type == 'Adoption':
                # نقل ملكية الحيوان إلى المتبني
                pet.owner = request_obj.sender 
                pet.save()
                
                # حذف منشور التبني
                AdoptionPost.objects.filter(pet=pet).delete()
                action_message = "Ownership transferred, pet removed from adoption list."
                activity_key = ADOPTION_APPROVED_KEY
                
            elif request_obj.request_type == 'Mate':
                # حذف منشور التزاوج
                MatingPost.objects.filter(pet=pet).delete()
                action_message = "Mating request approved, MatingPost deleted."
                activity_key = MATING_APPROVED_KEY
            else:
                activity_key = None

            # منح النقاط
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

            # حذف جميع طلبات التفاعل لهذا الحيوان بعد القبول (لأن العملية تمت)
            InteractionRequest.objects.filter(pet=pet).delete()
            
            return Response({
                "detail": f"Request accepted. Pet {pet.id} operation complete. {action_message}",
                "points_awarded_to_sender": points_awarded,
                "sender_current_points": sender_current_points
            }, status=status.HTTP_200_OK)

        # 4. منطق الرفض (Rejected)
        elif new_status == 'Rejected':
            
            # حذف الطلب المرفوض فقط من Inbox المالك
            request_id = request_obj.id
            request_obj.delete()

            return Response(
                {"detail": f"Request {request_id} rejected and deleted from your inbox."},
                status=status.HTTP_200_OK
            )
        
        # 5. حالة أخرى (مثل "Pending") - لا ينبغي الوصول إليها هنا
        else:
            return Response({"detail": "Status updated successfully."}, status=status.HTTP_200_OK)