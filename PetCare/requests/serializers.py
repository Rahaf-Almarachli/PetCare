from rest_framework import serializers
from .models import InteractionRequest
from pets.models import Pet 
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

# ----------------------------------------------------
# 1. Sender Detail Serializer
# ----------------------------------------------------
class SenderDetailSerializer(serializers.ModelSerializer):
    """
    Serializes sender details for the Request Details page.
    """
    location = serializers.CharField(source='location', read_only=True)
    phone_number = serializers.CharField(source='phone_number', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'location', 'phone_number'] 
        read_only_fields = ['id', 'full_name', 'location', 'phone_number']

# ----------------------------------------------------
# 2. Request Create Serializer (للمسار POST /create/)
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
# 3. Request Detail Serializer (للعرض والتفاصيل والـ Inbox)
# ----------------------------------------------------
class RequestDetailSerializer(serializers.ModelSerializer):
    """
    Serializer يُستخدم لعرض تفاصيل الطلب (للمرسل والمستقبل).
    """
    sender = SenderDetailSerializer(read_only=True)

    # حقول العرض الإضافية
    pet_name = serializers.CharField(source='pet.pet_name', read_only=True)
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    sender_location = serializers.CharField(source='sender.location', read_only=True)
    
    # attached_file كـ URLField للقراءة
    attached_file = serializers.URLField(read_only=True)


    class Meta:
        model = InteractionRequest
        fields = [
            'id', 'request_type', 'message', 'owner_response_message', 
            'attached_file', 'status', 'created_at', 'pet_name',
            'sender',  
            'sender_name', 'sender_location' 
        ]
        read_only_fields = ['id', 'request_type', 'message', 'owner_response_message', 
                            'attached_file', 'status', 'created_at', 'pet_name', 
                            'sender', 'sender_name', 'sender_location']