from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.shortcuts import get_object_or_404

# استيراد النموذج والـ Serializers
from .models import InteractionRequest
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
    serializer_class = RequestDetailSerializer # يستخدم الـ Serializer الموجز
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
        # إرجاع البيانات باستخدام Full Detail Serializer للعرض الكامل بعد الإنشاء
        response_serializer = RequestFullDetailSerializer(instance)
        return response_serializer.data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        response_data = self.perform_create(serializer)
        
        return Response(response_data, status=status.HTTP_201_CREATED)

# ----------------------------------------------------
# 4. View لتحديث حالة الطلب وإضافة الرد (فقط للمالك)
# ----------------------------------------------------
class RequestUpdateStatusView(APIView):
    """
    PATCH: تحديث حالة الطلب (قبول/رفض) وإضافة رسالة الرد من المالك.
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, id):
        request_obj = get_object_or_404(InteractionRequest, id=id)
        user = request.user

        if request_obj.receiver != user:
            return Response(
                {"detail": "You do not have permission to modify this request."},
                status=status.HTTP_403_FORBIDDEN
            )

        if 'status' not in request.data:
            return Response(
                {"detail": "Missing 'status' field in the request."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_status = request.data['status']
        owner_response_message = request.data.get('owner_response_message', request_obj.owner_response_message)

        request_obj.status = new_status
        request_obj.owner_response_message = owner_response_message
        
        request_obj.save(update_fields=['status', 'owner_response_message'])

        # نستخدم الـ Serializer التفصيلي لإرجاع الحالة المحدثة
        serializer = RequestFullDetailSerializer(request_obj) 
        return Response(serializer.data, status=status.HTTP_200_OK)