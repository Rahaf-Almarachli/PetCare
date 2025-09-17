from rest_framework import serializers
from .models import Vaccination
from pets.models import Pet  # يجب استيراد نموذج الحيوان الأليف

class VaccinationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vaccination
        fields = "__all__"
        read_only_fields = ['pet']