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
    Assumes 'full_name', 'location', and 'phone_number' are accessible on the User model.
    """
    # Assuming these fields are available on the User model
    location = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'location', 'phone_number'] 
        read_only_fields = ['id', 'full_name', 'location', 'phone_number']

# ----------------------------------------------------
# 2. Interaction Request Serializer (CREATE/LIST)
# ----------------------------------------------------
class InteractionRequestSerializer(serializers.ModelSerializer):
    """
    Serializer used for POST (Create) and GET (Inbox List).
    **Attached_file now expects a valid URL string.**
    """
    pet_id = serializers.IntegerField(write_only=True)
    
    pet_name = serializers.CharField(source='pet.pet_name', read_only=True)
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    sender_location = serializers.CharField(source='sender.location', read_only=True) 

    # 🟢 التعديل الرئيسي: تعريف attached_file كـ URLField 🟢
    attached_file = serializers.URLField(
        required=False, 
        allow_null=True, 
        allow_blank=True,
        max_length=500
    )

    class Meta:
        model = InteractionRequest
        fields = [
            'id', 'pet_id', 'request_type', 'message', 'owner_response_message', 
            'attached_file', 'status', 'created_at', 'pet_name', 'sender_name', 
            'sender_location'
        ]
        # owner_response_message is read-only when listing or creating
        read_only_fields = ['status', 'created_at', 'owner_response_message'] 


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
# 3. Request Detail Serializer (RETRIEVE/UPDATE)
# ----------------------------------------------------
class RequestDetailSerializer(InteractionRequestSerializer):
    """
    Serializer used for the detailed GET request and also for the PATCH response.
    """
    sender = SenderDetailSerializer(read_only=True)

    class Meta(InteractionRequestSerializer.Meta):
        fields = [
            'id', 'sender', 'request_type', 'message', 'owner_response_message', 
            'attached_file', 'status', 'created_at', 'pet_name', 'pet_id'
        ]
        read_only_fields = InteractionRequestSerializer.Meta.read_only_fields