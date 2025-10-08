from rest_framework import serializers
from .models import InteractionRequest
from pets.models import Pet 
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

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


class InteractionRequestSerializer(serializers.ModelSerializer):
    """
    Serializer used for POST (Create) and GET (Inbox List).
    """
    # Input field from Flutter (write_only)
    pet_id = serializers.IntegerField(write_only=True)
    
    # Output fields for the Inbox List display (read_only)
    pet_name = serializers.CharField(source='pet.pet_name', read_only=True)
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    sender_location = serializers.CharField(source='sender.location', read_only=True) 

    class Meta:
        model = InteractionRequest
        fields = [
            'id', 'pet_id', 'request_type', 'message', 'attached_file', 'status', 
            'created_at', 'pet_name', 'sender_name', 'sender_location'
        ]
        read_only_fields = ['status', 'created_at']

    def validate_pet_id(self, value):
        user = self.context['request'].user
        try:
            pet = Pet.objects.get(id=value)
        except Pet.DoesNotExist:
            raise serializers.ValidationError("Pet not found.")
        
        # Prevent user from requesting their own pet
        if pet.owner == user:
            raise serializers.ValidationError("Cannot send a request for your own pet.")
        
        return value

    @transaction.atomic
    def create(self, validated_data):
        pet_id = validated_data.pop('pet_id')
        pet = Pet.objects.get(id=pet_id)
        user = self.context['request'].user
        
        # Check for existing pending request
        if InteractionRequest.objects.filter(sender=user, pet=pet, status='Pending').exists():
             raise serializers.ValidationError({"detail": "You already have a pending request for this pet."})

        # Set the sender (current user) and receiver (pet owner)
        validated_data['sender'] = user
        validated_data['receiver'] = pet.owner 
        validated_data['pet'] = pet
        
        request = InteractionRequest.objects.create(**validated_data)
        
        # --- NOTIFICATION HOOK: WebSocket/FCM calls go here later ---

        return request


class RequestDetailSerializer(InteractionRequestSerializer):
    """
    Serializer used for the detailed GET request (Request Details page).
    Includes the detailed Sender information.
    """
    sender = SenderDetailSerializer(read_only=True)

    class Meta(InteractionRequestSerializer.Meta):
        fields = [
            'id', 'sender', 'request_type', 'message', 'attached_file', 'status', 
            'created_at', 'pet_name', 'pet_id'
        ]
        read_only_fields = InteractionRequestSerializer.Meta.read_only_fields
