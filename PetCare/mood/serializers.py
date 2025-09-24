# petcare/serializers.py
from rest_framework import serializers
from .models import Mood
from pets.models import Pet
from django.shortcuts import get_object_or_404

class MoodCreateSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(write_only=True)
    
    class Meta:
        model = Mood
        fields = ['pet_name', 'mood', 'notes', 'date']
        extra_kwargs = {
            'notes': {'required': False},
            'date': {'required': True}
        }

    def create(self, validated_data):
        pet_name = validated_data.pop('pet_name')

        try:
            # تم تعديل هذا السطر
            pet = Pet.objects.get(pet_name=pet_name, owner=self.context['request'].user)
        except Pet.DoesNotExist:
            raise serializers.ValidationError({"pet_name": "Pet with this name does not exist for the current user."})

        mood_instance = Mood.objects.create(
            pet=pet,
            mood=validated_data.get('mood'),
            notes=validated_data.get('notes'),
            date=validated_data.get('date')
        )
        return mood_instance