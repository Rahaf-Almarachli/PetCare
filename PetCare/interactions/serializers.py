from rest_framework import serializers
# تأكد من استيراد الموديلات الصحيحة حسب مكانها في مشروعك
from .models import InteractionRequest
from pets.models import Pet 
from django.contrib.auth import get_user_model
from django.db import transaction

# ⚠️ تم إبقاء الاستيراد لكن الكود لا يستخدمه في دالة create الآن ⚠️
from notifications.utils import send_pushy_notification 

User = get_user_model()

# ----------------------------------------------------
# 1. Sender Detail Serializer
# ----------------------------------------------------
class SenderDetailSerializer(serializers.ModelSerializer):
    """
    Serializes sender details (Full Name, Location, Phone) for Detail views.
    """
    location = serializers.CharField(read_only=True) 
    phone_number = serializers.SerializerMethodField() 
    full_name = serializers.CharField(read_only=True) 
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'location', 'phone_number'] 
        read_only_fields = fields

    def get_phone_number(self, obj):
        return getattr(obj, 'phone', '') or ''

# ----------------------------------------------------
# 2. Request Create Serializer (المعدل: تم حذف الإشعار)
# ----------------------------------------------------
class RequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer مخصص لإنشاء طلب جديد، الآن لا يرسل الإشعار بنفسه.
    """
    pet_id = serializers.IntegerField(write_only=True)
    attached_file = serializers.URLField(
        required=False, 
        allow_null=True, 
        allow_blank=True,
        max_length=500
    )

    class Meta:
        model = InteractionRequest
        fields = ['pet_id', 'request_type', 'message', 'attached_file']

    def validate_pet_id(self, value):
        user = self.context['request'].user
        try:
            pet = Pet.objects.get(id=value)
        except Pet.DoesNotExist:
            raise serializers.ValidationError("Pet not found.")
        
        if pet.owner == user:
            raise serializers.ValidationError("Cannot send a request for your own pet.")
        
        if InteractionRequest.objects.filter(sender=user, pet=pet, status='Pending').exists():
            raise serializers.ValidationError("You already have a pending request for this pet.")

        return value

    @transaction.atomic
    def create(self, validated_data):
        pet_id = validated_data.pop('pet_id')
        pet = Pet.objects.get(id=pet_id)
        user = self.context['request'].user
        
        validated_data['sender'] = user
        validated_data['receiver'] = pet.owner 
        validated_data['pet'] = pet
        
        # 1. إنشاء وحفظ كائن الطلب (فقط)
        request = InteractionRequest.objects.create(**validated_data)

        # 2. ❌ تم إزالة منطق الإشعار العربي من هنا لمنع التكرار
        
        return request

# ----------------------------------------------------
# 3. Request Detail Serializer (للعرض الموجز/القائمة)
# ----------------------------------------------------
class RequestDetailSerializer(serializers.ModelSerializer):
    """
    Serializer يُستخدم لعرض التفاصيل الموجزة (Inbox List).
    """
    sender_first_name = serializers.SerializerMethodField()
    sender_location = serializers.CharField(source='sender.location', read_only=True)
    request_summary_text = serializers.SerializerMethodField()
    
    class Meta:
        model = InteractionRequest
        fields = ['id', 'sender_first_name', 'sender_location', 'request_summary_text', 'request_type']
        read_only_fields = fields
    
    def get_sender_first_name(self, obj):
        full_name = getattr(obj.sender, 'full_name', '')
        if full_name:
            return full_name.split(' ')[0]
        return ""
    
    def get_request_summary_text(self, obj):
        pet_name = obj.pet.pet_name
        if obj.request_type == 'Mate':
            return f"Requesting to mate {pet_name}"
        elif obj.request_type == 'Adoption':
            return f"Requesting to adopt {pet_name}"
        return ""

# ----------------------------------------------------
# 4. Request Full Detail Serializer (للعرض التفصيلي)
# ----------------------------------------------------
class RequestFullDetailSerializer(serializers.ModelSerializer):
    """
    Serializer يُستخدم لعرض التفاصيل الكاملة للطلب (Request Details Screen).
    """
    sender = SenderDetailSerializer(read_only=True)
    
    class Meta:
        model = InteractionRequest
        fields = ['id', 'sender', 'message', 'attached_file'] 
        read_only_fields = fields


# ----------------------------------------------------
# 5. Request Update Serializer (لتحديث الحالة)
# ----------------------------------------------------
class RequestUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer يُستخدم لتحديث حالة الطلب ورسالة الرد من المالك.
    """
    class Meta:
        model = InteractionRequest
        fields = ('status', 'owner_response_message')
        read_only_fields = ('request_type', 'message', 'attached_file')