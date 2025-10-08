from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404

# الاستيرادات اللازمة
from .models import InteractionRequest
from .serializers import RequestCreateSerializer, RequestDetailSerializer, SenderDetailSerializer
# 👆 تم تغيير InteractionRequestSerializer إلى RequestCreateSerializer 👆

# ----------------------------------------------------
# 1. View لعرض قائمة الطلبات (Inbox)
# ----------------------------------------------------
class RequestInboxListView(generics.ListAPIView):
    """
    GET: عرض جميع الطلبات الواردة للمستخدم الحالي (بصفته المالك/المستقبل).
    """
    serializer_class = RequestDetailSerializer # يستخدم لعرض تفاصيل الطلب السريع
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # جلب الطلبات التي يكون فيها المستخدم الحالي هو المستقبل (Receiver)
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
    يسمح للمرسل أو المستقبل (المالك) برؤية الطلب.
    """
    serializer_class = RequestDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        # يسمح للمستخدم برؤية الطلبات التي هو مرسلها أو مستقبلها
        return InteractionRequest.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender', 'pet')

# ----------------------------------------------------
# 3. View لإنشاء طلب جديد
# ----------------------------------------------------
class CreateInteractionRequestView(generics.CreateAPIView):
    """
    POST: إنشاء طلب تفاعل جديد (تبني/تزاوج).
    """
    # 🟢 نستخدم Serializer المخصص للإنشاء 🟢
    serializer_class = RequestCreateSerializer 
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # يتم تخزين المنطق المعقد للـ create في الـ Serializer
        instance = serializer.save()
        
        # لضمان أن الاستجابة (Response) تعرض جميع التفاصيل المنسقة
        # نستخدم RequestDetailSerializer لإرجاع البيانات بعد الحفظ.
        response_serializer = RequestDetailSerializer(instance)
        return response_serializer.data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # يتم استخدام perform_create للحفظ والحصول على كائن الاستجابة المنسق
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

        # التحقق من أن المستخدم الحالي هو المالك/المستقبل للطلب
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
        owner_response_message = request.data.get('owner_response_message', '')

        # تحديث الحقول مباشرة
        request_obj.status = new_status
        request_obj.owner_response_message = owner_response_message
        request_obj.save(update_fields=['status', 'owner_response_message'])

        # إرجاع تفاصيل الطلب المحدثة باستخدام RequestDetailSerializer
        serializer = RequestDetailSerializer(request_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)