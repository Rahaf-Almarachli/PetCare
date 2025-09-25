# alerts/serializers.py
from rest_framework import serializers
from .models import Alert
from pets.models import Pet


class AlertSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(write_only=True)  # المستخدم يرسل اسم الحيوان
    pet = serializers.CharField(source="pet.pet_name", read_only=True)

    class Meta:
        model = Alert
        fields = ['id', 'pet_name', 'pet', 'name', 'time', 'is_active']

    def create(self, validated_data):
        request = self.context['request']
        pet_name = validated_data.pop('pet_name')

        try:
            pet = Pet.objects.get(pet_name=pet_name, owner=request.user)
        except Pet.DoesNotExist:
            raise serializers.ValidationError({"pet_name": "Pet not found or does not belong to you."})

        alert = Alert.objects.create(
            pet=pet,
            owner=request.user,
            name=validated_data['name'],
            time=validated_data['time'],
            is_active=validated_data.get('is_active', True)  # افتراضيًا ON
        )
        return alert
