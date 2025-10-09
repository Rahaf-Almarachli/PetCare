from rest_framework import serializers
from .models import InteractionRequest
# تأكد من استيراد Pet بشكل صحيح، بناءً على مكان الـ Model
from pets.models import Pet 
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

# ----------------------------------------------------
# 1. Sender Detail Serializer (تفاصيل المرسل الكاملة)
# ----------------------------------------------------
class SenderDetailSerializer(serializers.ModelSerializer):
    """
    Serializes sender details (Full Name, Location, Phone) for Detail views.
    """
    # تم إزالة source المكرر
    location = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'location', 'phone_number'] 
        read_only_fields = ['id', 'full_name', 'location', 'phone_number']

# ----------------------------------------------------
# 2. Request Create Serializer (لإنشاء الطلب)
# ----------------------------------------------------
class RequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer مخصص لإنشاء طلب جديد.
    """
    pet_id = serializers.IntegerField(write_only=True)
    
    # attached_file كـ URLField
    attached_file = serializers.URLField(
        required=False, 
        allow_null=True, 
        allow_blank=True,
        max_length=500
    )

    class Meta:
        model = InteractionRequest
        fields = [
            'pet_id', 'request_type', 'message', 'attached_file'
        ]

    def validate_pet_id(self, value):
        user = self.context['request'].user
        try:
            pet = Pet.objects.get(id=value)
        except Pet.DoesNotExist:
            raise serializers.ValidationError("Pet not found.")
        
        if pet.owner == user:
            raise serializers.ValidationError("Cannot send a request for your own pet.")
        
        return value

    @transaction.atomic
    def create(self, validated_data):
        pet_id = validated_data.pop('pet_id')
        pet = Pet.objects.get(id=pet_id)
        user = self.context['request'].user
        
        if InteractionRequest.objects.filter(sender=user, pet=pet, status='Pending').exists():
             raise serializers.ValidationError({"detail": "You already have a pending request for this pet."})

        validated_data['sender'] = user
        validated_data['receiver'] = pet.owner 
        validated_data['pet'] = pet
        
        request = InteractionRequest.objects.create(**validated_data)
        
        return request

# ----------------------------------------------------
# 3. Request Detail Serializer (للعرض الموجز/Inbox List)
# ----------------------------------------------------
class RequestDetailSerializer(serializers.ModelSerializer):
    """
    Serializer يُستخدم لعرض التفاصيل الموجزة (Inbox List).
    """
    sender_first_name = serializers.SerializerMethodField()
    sender_location = serializers.CharField(source='sender.location', read_only=True)
    request_summary_text = serializers.SerializerMethodField()
    

    def get_sender_first_name(self, obj):
        full_name = obj.sender.full_name
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


    class Meta:
        model = InteractionRequest
        fields = [
            'id', 
            'sender_first_name',     
            'sender_location',       
            'request_summary_text',  
            'request_type',          
        ]
        read_only_fields = fields

# ----------------------------------------------------
# 4. Request Full Detail Serializer (للعرض التفصيلي)
# ----------------------------------------------------
class RequestFullDetailSerializer(serializers.ModelSerializer):
    """
    Serializer يُستخدم لعرض التفاصيل الكاملة للطلب (Request Details Screen).
    يعرض فقط: تفاصيل المرسل (الاسم، الموقع، الهاتف)، الرسالة، والملف المرفق.
    """
    # نستخدم SenderDetailSerializer لعرض الاسم الكامل، الموقع، ورقم الهاتف
    sender = SenderDetailSerializer(read_only=True)
    
    # الملف المرفق
    attached_file = serializers.URLField(read_only=True) 

    class Meta:
        model = InteractionRequest
        # 🟢 الحقول الخمسة المطلوبة فقط 🟢
        fields = [
            'sender',          # يحتوي على: full_name, location, phone_number
            'message',         # رسالة الطلب
            'attached_file',   # الملف المرفق
        ]
        read_only_fields = fields