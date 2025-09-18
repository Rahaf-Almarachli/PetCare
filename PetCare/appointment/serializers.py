from rest_framework import serializers
from .models import Appointment
from pets.serializers import PetSerializer
from pets.models import Pet

class AppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Appointment model.
    """
    # حقل للقراءة فقط لإظهار ID الحيوان الأليف
    pet_id = serializers.ReadOnlyField(source='pet.id')

    class Meta:
        model = Appointment
        fields = ['id', 'pet', 'service', 'date', 'time', 'provider', 'pet_id']
        extra_kwargs = {
            # جعل حقل 'pet' للكتابة فقط لضمان أن المستخدم يرسل الـ ID.
            'pet': {'write_only': True, 'required': True}
        }
    
    def validate_pet(self, value):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is not available.")
        user = request.user
        if not Pet.objects.filter(id=value.id, owner=user).exists():
            raise serializers.ValidationError("Pet does not exist or does not belong to the user.")
        return value

    def create(self, validated_data):
        return Appointment.objects.create(**validated_data)
