from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.db import transaction 

# استيراد النماذج
from .models import InteractionRequest
from pets.models import Pet 
# 🟢 التعديل: استيراد نموذج AdoptionPost
from adoption.models import AdoptionPost 
from .serializers import (
    RequestCreateSerializer, 
    RequestDetailSerializer, 
    RequestFullDetailSerializer 
)

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
        response_serializer = RequestFullDetailSerializer(instance)
        return response_serializer.data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        response_data = self.perform_create(serializer)
        
        return Response(response_data, status=status.HTTP_201_CREATED)

# ----------------------------------------------------
# 4. View لتحديث حالة الطلب (المعدَّل)
# ----------------------------------------------------
class RequestUpdateStatusView(APIView):
    """
    PATCH: تحديث حالة الطلب (قبول/رفض) وضمان إزالة الحيوان من قائمة التبني.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic # لضمان سلامة قاعدة البيانات
    def patch(self, request, id):
        request_obj = get_object_or_404(InteractionRequest, id=id)
        user = request.user

        # 1. التحقق من الصلاحيات
        if request_obj.receiver != user:
            return Response(
                {"detail": "You do not have permission to modify this request."},
                status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get('status')
        pet = request_obj.pet
        
        # التحقق من الحالة
        if not new_status or new_status not in ['Accepted', 'Rejected']:
            return Response({"detail": "Invalid or missing 'status' field (must be Accepted or Rejected)."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. تحديث حالة الطلب
        request_obj.status = new_status
        request_obj.save(update_fields=['status']) 


        if new_status == 'Accepted':
            
            # أ. منطق التعامل مع حالة الحيوان حسب نوع الطلب
            if request_obj.request_type == 'Adoption':
                
                # 1. نقل ملكية الحيوان إلى المتبني (المرسل)
                pet.owner = request_obj.sender 
                pet.save()
                
                # 🟢 التعديل الرئيسي: حذف منشور التبني 🟢
                try:
                    AdoptionPost.objects.get(pet=pet).delete()
                    action_message = "ownership transferred, pet removed from adoption list, and all requests deleted."
                except AdoptionPost.DoesNotExist:
                    # هذه الحالة تحدث إذا تم قبول طلب لحيوان لم يعد لديه منشور تبني.
                    action_message = "ownership transferred. AdoptionPost was already removed or didn't exist."
                
            elif request_obj.request_type == 'Mate':
                # في حالة التزاوج، يبقى المالك كما هو ولا يتأثر منشور التبني.
                pass
                action_message = "Mating request approved and all requests deleted."
            
            # ب. حذف جميع طلبات التفاعل لهذا الحيوان
            InteractionRequest.objects.filter(pet=pet).delete()
            
            # ج. الرد بعد العملية
            return Response(
                {"detail": f"Request accepted. Pet {pet.id} {action_message}"},
                status=status.HTTP_200_OK
            )

        elif new_status == 'Rejected':
            
            # د. حذف الطلب المرفوض فقط من Inbox المالك
            request_id = request_obj.id
            request_obj.delete()

            # هـ. الرد بعد العملية
            return Response(
                {"detail": f"Request {request_id} rejected and deleted from inbox."},
                status=status.HTTP_200_OK
            )
        
        else:
            # يجب أن لا يصل الكود إلى هنا
            serializer = RequestFullDetailSerializer(request_obj) 
            return Response(serializer.data, status=status.HTTP_200_OK)