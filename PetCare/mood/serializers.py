from rest_framework import serializers
from .models import Mood

class MoodCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mood
        fields = ['mood', 'notes', 'pet']  # ما في داعي يرسل date


class MoodHistorySerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)

    class Meta:
        model = Mood
        fields = ['pet_name', 'date', 'mood', 'notes']
