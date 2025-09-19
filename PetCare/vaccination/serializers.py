from rest_framework import serializers
from .models import Vaccination
from pets.models import Pet

class VaccinationSerializer(serializers.ModelSerializer):
    # حقل للقراءة فقط لإظهار اسم الحيوان الأليف
    pet_name = serializers.ReadOnlyField(source='pet.pet_name')
    
    class Meta:
        model = Vaccination
        fields = ['id', 'vacc_name', 'vacc_date', 'vacc_certificate', 'pet', 'pet_name']
        extra_kwargs = {
            # إخفاء حقل 'pet' من الإدخال لكن إتاحته للعرض
            'pet': {'write_only': True}
        }
