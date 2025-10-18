from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.urls import reverse 

import qrcode
from io import BytesIO
import cloudinary.uploader

from .models import Pet
from .serializers import PetSerializer, PetQRCodeDetailSerializer


# ---------------------------------------------------------------------
# 1. Pet ViewSet (لإدارة الحيوانات الأليفة - خاص بالمالك)
# ---------------------------------------------------------------------
class PetViewSet(viewsets.ModelViewSet):
    """إدارة عمليات CRUD للحيوانات الأليفة وتوليد الـ QR code."""
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # 1. حفظ الحيوان الأليف لأول مرة لتوليد الـ ID والـ QR_Token
        pet = serializer.save(owner=self.request.user) 
        
        # 2. بناء رابط الـ API Lookup الذي سيتم وضعه في الـ QR code
        # 💥 هذا الرابط هو الذي سيعيده الماسح (Scanner) في Flutter
        info_path = reverse('pet-qr-lookup', kwargs={'qr_token': pet.qr_token}) 
        destination_url = self.request.build_absolute_uri(info_path) # رابط الـ API العام
        
        # 3. توليد رمز QR
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(destination_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 4. حفظ الصورة ورفعها إلى Cloudinary
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # نستخدم اسم ملف فريد لـ Cloudinary
        public_id = f"qr_{pet.id}_{pet.qr_token}"
        upload_result = cloudinary.uploader.upload(
            buffer, 
            folder="pet_qr_codes",
            public_id=public_id,
            resource_type="image"
        )
        
        # 5. تحديث النموذج بروابط QR النهائية وحفظه مرة أخرى
        pet.qr_url = destination_url # رابط الـ API Lookup
        pet.qr_code_image = upload_result.get('secure_url') # رابط صورة الـ QR التي تُعرض في Flutter
        pet.save(update_fields=['qr_url', 'qr_code_image'])


# ---------------------------------------------------------------------
# 2. Pet QR Code Lookup View (الـ API المنفصل لـ Flutter)
# ---------------------------------------------------------------------
class PetQRCodeLookupView(generics.RetrieveAPIView):
    """
    GET: يسترجع اسم الحيوان وصورته ورابط صورة الـ QR بناءً على qr_token.
    يُستخدم لعرض بيانات الـ QR في تطبيق Flutter (لا يحتاج لمصادقة).
    """
    queryset = Pet.objects.all()
    serializer_class = PetQRCodeDetailSerializer
    
    # تحديد الحقل الذي سيستخدم في URL للبحث
    lookup_field = 'qr_token' 

    def retrieve(self, request, *args, **kwargs):
        try:
            # البحث عن الحيوان الأليف باستخدام الـ qr_token من الـ URL
            instance = self.get_object()
        except NotFound:
            return Response(
                {"detail": "QR Code Invalid or Pet Not Found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # استخدام Serializer الجديد لعرض البيانات المطلوبة فقط (اسم، صورة الحيوان، صورة الـ QR)
        serializer = self.get_serializer(instance)
        
        return Response(serializer.data, status=status.HTTP_200_OK)