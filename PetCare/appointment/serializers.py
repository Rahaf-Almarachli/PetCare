from rest_framework import serializers
from .models import Appointment
from pets.serializers import PetSerializer
from pets.models import Pet

class AppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Appointment model.
    """
    # حقل للقراءة فقط لإظهار معلومات الحيوان الأليف المرتبط بالموعد
    pet_details = PetSerializer(source='pet', read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'pet', 'service', 'date', 'time', 'provider', 'pet_details']

    def validate_pet(self, value):
        """
        Validate that the pet exists and belongs to the current user.
        """
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is not available.")
        
        user = request.user
        
        # التحقق من أن الحيوان الأليف موجود وينتمي للمستخدم
        if not Pet.objects.filter(id=value.id, owner=user).exists():
            raise serializers.ValidationError("Pet does not exist or does not belong to the user.")
        
        return value

    def create(self, validated_data):
        """
        Create a new appointment and associate it with the pet.
        """
        return Appointment.objects.create(**validated_data)
