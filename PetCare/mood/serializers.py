from rest_framework import serializers
from .models import Mood
from pets.models import Pet

class MoodCreateSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(write_only=True)

    class Meta:
        model = Mood
        fields = ['pet_name', 'mood', 'notes']

    def create(self, validated_data):
        request = self.context['request']
        pet_name = validated_data.pop('pet_name')

        try:
            pet = Pet.objects.get(pet_name=pet_name, owner=request.user)
        except Pet.DoesNotExist:
            raise serializers.ValidationError({"pet_name": "Pet not found or does not belong to the user."})

        return Mood.objects.create(pet=pet, **validated_data)


class MoodResponseSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.pet_name', read_only=True)

    class Meta:
        model = Mood
        fields = ['pet_name', 'mood', 'date', 'notes']
