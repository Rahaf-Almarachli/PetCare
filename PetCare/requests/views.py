from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.db import transaction # 🟢 استيراد الـ transaction 🟢

# استيراد النموذج والـ Serializers
from .models import InteractionRequest
# يجب استيراد نموذج الحيوان الأليف (Pet) للوصول إليه
from pets.models import Pet 
from .serializers import (
    RequestCreateSerializer, 
    RequestDetailSerializer, 
    RequestFullDetailSerializer 
)

# ----------------------------------------------------
# 1. View لعرض قائمة الطلبات (Inbox)
# ----------------------------------------------------
class RequestInboxListView(generics.ListAPIView):
    # ... (الكود كما هو)
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
    # ... (الكود كما هو)
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
    # ... (الكود كما هو)
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
# 4. View لتحديث حالة الطلب وإضافة الرد (فقط للمالك) - المعدل
# ----------------------------------------------------
class RequestUpdateStatusView(APIView):
    """
    PATCH: تحديث حالة الطلب (قبول/رفض).
    1. عند القبول، يتم حذف الحيوان من العرض.
    2. يتم حذف الطلب نفسه بعد المعالجة.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic # 🟢 لضمان تنفيذ العمليتين (التحديث والحذف) أو عدم تنفيذهما معاً 🟢
    def patch(self, request, id):
        request_obj = get_object_or_404(InteractionRequest, id=id)
        user = request.user

        # التحقق من الصلاحيات
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
        pet = request_obj.pet
        
        # 1. تحديث حالة الحيوان (فقط عند القبول)
        if new_status == 'Accepted':
            # 💡 يتم افتراض أن النموذج Pet لديه حقل يتحكم في عرضه (مثل is_available)
            # إذا كان الحقل في نموذج Pet اسمه is_available, فيمكنك تعديله:
            # pet.is_available = False 
            # pet.save()
            
            # 💡 إذا كنت تريد حذفه فعليًا من قاعدة البيانات (وهو خيار قوي لا يفضل عادةً):
            # pet.delete()

            # 💡 التعديل الأفضل: ربط الحيوان بالمستخدم الجديد (لعمليات التبني)
            if request_obj.request_type == 'Adoption':
                pet.owner = request_obj.sender # نقل ملكية الحيوان إلى المرسل
                # 💡 ربما تحتاج لتعديل حقل يدل على عدم عرضه (مثلاً 'is_listed_for_adoption')
                # pet.is_listed_for_adoption = False 
                pet.save()
            
            # إذا كان الطلب 'Mate'، لا يتم حذف الحيوان، لكن قد ترغب في تحديث حالته.
            pass # نتركها حالياً كما هي للتزاوج

        # 2. تحديث رسالة الرد وحفظ الطلب
        request_obj.status = new_status
        request_obj.owner_response_message = request.data.get('owner_response_message', request_obj.owner_response_message)
        request_obj.save()

        # 3. حذف الطلب من قائمة الطلبات (بعد قبوله/رفضه)
        request_id = request_obj.id
        request_obj.delete()

        # 4. إرجاع رد ناجح (مع الإشارة إلى أن الطلب حُذف)
        # بما أن الكائن حُذف، لا يمكننا تمريره إلى Serializer.
        # لذا نرسل رسالة نجاح بسيطة.
        return Response(
            {"detail": f"Request {request_id} successfully processed and deleted."},
            status=status.HTTP_200_OK
        )