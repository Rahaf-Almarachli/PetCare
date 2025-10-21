from rest_framework import serializers
from .models import Mood
from pets.models import Pet
from django.utils import timezone

class MoodCreateSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(write_only=True)

    class Meta:
        model = Mood
        fields = ['pet_name', 'mood',]

    def create(self, validated_data):
        pet_name = validated_data.pop('pet_name')
        request = self.context['request']

        try:
            pet = Pet.objects.get(pet_name=pet_name, owner=request.user)
        except Pet.DoesNotExist:
            raise serializers.ValidationError({"pet_name": "Pet not found or does not belong to you."})

        today = timezone.now().date()

        mood = Mood.objects.create(
            pet=pet,
            mood=validated_data['mood'],
            date=today
        )
        return mood


class MoodResponseSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.pet_name', read_only=True)
    date = serializers.SerializerMethodField()

    class Meta:
        model = Mood
        fields = ['pet_name', 'mood', 'date',]

    def get_date(self, obj):
        if hasattr(obj.date, "date"):
            return obj.date.date().isoformat()
        return obj.date.isoformat()


class MoodHistorySerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.pet_name', read_only=True)
    date = serializers.SerializerMethodField()

    class Meta:
        model = Mood
        fields = ['pet_name', 'mood', 'date',]

    def get_date(self, obj):
        if hasattr(obj.date, "date"):
            return obj.date.date().isoformat()
        return obj.date.isoformat()
