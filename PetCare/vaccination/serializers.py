from rest_framework import serializers
from .models import Vaccination

class VaccinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vaccination
        fields = "__all__"   # pet, vacc_name, vacc_date, vacc_certificate
