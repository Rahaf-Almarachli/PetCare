from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import InteractionRequest
# ...
# بقية الاستيرادات الأخرى
from .serializers import RequestCreateSerializer, RequestDetailSerializer 
# ...
# 🟢 الاستيراد الصحيح للـ Serializers الجديدة 🟢
from .serializers import RequestCreateSerializer, RequestDetailSerializer

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
    serializer_class = RequestDetailSerializer
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
    # 🟢 استخدام Serializer الإنشاء 🟢
    serializer_class = RequestCreateSerializer 
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save()
        # إرجاع البيانات باستخدام Detail Serializer للعرض الكامل
        response_serializer = RequestDetailSerializer(instance)
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
    مخصص للمستقبل (المالك) فقط.
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, id):
        request_obj = get_object_or_404(InteractionRequest, id=id)
        user = request.user

        # 🟢 منطق التحقق من الأذونات (403 Forbidden) 🟢
        if request_obj.receiver != user:
            return Response(
                {"detail": "You do not have permission to modify this request."},
                status=status.HTTP_403_FORBIDDEN
            )

        # التحقق من أن الحقول المطلوبة موجودة
        if 'status' not in request.data:
            return Response(
                {"detail": "Missing 'status' field in the request."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_status = request.data['status']
        # إذا لم يتم إرسال owner_response_message، استخدم الرسالة الحالية
        owner_response_message = request.data.get('owner_response_message', request_obj.owner_response_message)

        # تحديث الحقول
        request_obj.status = new_status
        request_obj.owner_response_message = owner_response_message
        
        # 🟢 يتم الآن الحفظ بنجاح لأن الحقل موجود في الـ Model 🟢
        request_obj.save(update_fields=['status', 'owner_response_message'])

        serializer = RequestDetailSerializer(request_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)