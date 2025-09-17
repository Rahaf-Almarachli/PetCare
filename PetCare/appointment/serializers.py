from rest_framework import serializers
from .models import Appointment
from pets.serializers import PetSerializer

class AppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Appointment model.
    """
    # حقل للقراءة فقط لإظهار معلومات الحيوان الأليف المرتبط بالموعد
    pet_details = PetSerializer(source='pet', read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'pet', 'service', 'date', 'time', 'provider', 'pet_details']
        # جعل حقل pet مطلوبًا عند الإنشاء فقط
        extra_kwargs = {
            'pet': {'required': True}
        }