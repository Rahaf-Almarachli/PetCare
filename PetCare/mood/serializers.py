from rest_framework import serializers
from .models import Mood
from pets.models import Pet
from django.shortcuts import get_object_or_404

class MoodCreateSerializer(serializers.ModelSerializer):
    """
    Serializer لإنشاء سجل مزاج جديد.
    يتطلب اسم الحيوان الأليف لربطه بالمستخدم.
    """
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
        request_user = self.context['request'].user
        
        try:
            pet = Pet.objects.get(pet_name=pet_name, owner=request_user)
        except Pet.DoesNotExist:
            raise serializers.ValidationError({"pet_name": "Pet with this name does not exist for the current user."})

        mood_instance = Mood.objects.create(
            pet=pet,
            **validated_data
        )
        return mood_instance

class MoodHistorySerializer(serializers.ModelSerializer):
    """
    Serializer للقراءة فقط، يستخدم لعرض سجلات المزاج.
    يضم اسم الحيوان الأليف من خلال العلاقة.
    """
    pet_name = serializers.CharField(source='pet.pet_name', read_only=True)
    
    class Meta:
        model = Mood
        fields = ['pet_name', 'mood', 'notes', 'date']