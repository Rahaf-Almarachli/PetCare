from rest_framework import viewsets, permissions
from .models import Pet
from .serializers import PetSerializer

# 💥 استيرادات جديدة لـ QR code و Cloudinary
import qrcode
from io import BytesIO
import cloudinary.uploader
from django.urls import reverse 
from django.shortcuts import get_object_or_404, render


class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # 1. حفظ الحيوان الأليف لأول مرة لتوليد الـ ID والـ QR_Token
        pet = serializer.save(owner=self.request.user) 
        
        # 2. بناء رابط صفحة معلومات الحيوان الأليف
        info_path = reverse('pet-info-detail', kwargs={'token': pet.qr_token}) 
        # تأكد من استخدام الرابط المطلق (Absolute URL) لنشر الـ QR code
        destination_url = self.request.build_absolute_uri(info_path)
        
        # 3. توليد رمز QR
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(destination_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 4. حفظ الصورة في ذاكرة مؤقتة ورفعها إلى Cloudinary
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        upload_result = cloudinary.uploader.upload(
            buffer, 
            folder="pet_qr_codes",
            public_id=f"qr_{pet.id}" 
        )
        
        # 5. تحديث النموذج بروابط QR النهائية وحفظه مرة أخرى
        pet.qr_url = destination_url
        pet.qr_code_image = upload_result.get('secure_url')
        pet.save(update_fields=['qr_url', 'qr_code_image'])


# 💥 دالة View لصفحة معلومات الحيوان الأليف (التي يفتحها الـ QR code)
# ملاحظة: يجب أن يحتوي نموذج المستخدم (User) على 'location' و 'phone'.
def pet_info_view(request, token):
    pet = get_object_or_404(Pet, qr_token=token)
    owner = pet.owner

    context = {
        'pet_name': pet.pet_name,
        'pet_type': pet.pet_type,
        'owner_name': owner.username, 
        # يجب استبدالها بـ owner.location و owner.phone إذا كانت موجودة
        'owner_location': getattr(owner, 'location', 'موقع غير متوفر'), 
        'owner_phone': getattr(owner, 'phone', 'هاتف غير متوفر'),       
        'pet_photo_url': pet.pet_photo,
        'pet': pet,
    }
    # ⚠️ يجب إنشاء ملف 'pet_info.html' في 'pets/templates/pets/'
    return render(request, 'pets/pet_info.html', context)