from rest_framework import serializers
from .models import Mood
from pets.models import Pet
from django.utils import timezone

class MoodCreateSerializer(serializers.ModelSerializer):
    pet_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Mood
        fields = ['pet_id', 'mood',]

    def create(self, validated_data):
        pet_id = validated_data.pop('pet_id')
        request = self.context['request']

        try:
            pet = Pet.objects.get(id=pet_id, owner=request.user)
        except Pet.DoesNotExist:
            raise serializers.ValidationError({"pet_id": "Pet not found or does not belong to you."})

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
    

class LatestMoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mood
        fields = ['mood']
