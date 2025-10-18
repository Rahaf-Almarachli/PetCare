from rest_framework import serializers
from .models import Pet

# ---------------------------------------------------------------------
# Serializer 1: PetSerializer (لإدارة الحيوانات الأليفة - API الخاص)
# ---------------------------------------------------------------------
class PetSerializer(serializers.ModelSerializer):
    """Serializer أساسي لإدارة بيانات الحيوان الأليف (للمالك)."""
    age = serializers.IntegerField(read_only=True)
    pet_photo = serializers.URLField(required=False, max_length=500) 
    
    # حقول QR للقراءة فقط
    qr_token = serializers.UUIDField(read_only=True)
    qr_url = serializers.URLField(read_only=True)
    qr_code_image = serializers.URLField(read_only=True)
    
    class Meta:
        model = Pet
        fields = ['id', 'owner', 'pet_name', 'pet_type', 'pet_color', 'pet_gender', 'pet_birthday', 'pet_photo', 
                  'age', 'qr_token', 'qr_url', 'qr_code_image']
        read_only_fields = ['owner', 'qr_token', 'qr_url', 'qr_code_image']


# ---------------------------------------------------------------------
# Serializer 2: PetQRCodeDetailSerializer (لـ API العام - لـ Flutter)
# ---------------------------------------------------------------------
class PetQRCodeDetailSerializer(serializers.ModelSerializer):
    """
    Serializer يعرض اسم الحيوان وصورته ورابط صورة QR (لصفحة الـ QR في Flutter).
    يُستخدم في الـ Public QR Endpoint.
    """
    class Meta:
        model = Pet
        # يجب أن نعرض كل من اسم الحيوان، صورته، وصورة الـ QR نفسها
        fields = ['pet_name', 'pet_photo', 'qr_code_image']
        read_only_fields = fields