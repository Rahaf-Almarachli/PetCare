from rest_framework import serializers
from pets.models import Pet
from .models import MatingPost
from pets.serializers import PetSerializer

class MatingPostSerializer(serializers.ModelSerializer):
    existing_pet_id = serializers.IntegerField(write_only=True, required=False)
    new_pet_data = PetSerializer(write_only=True, required=False)

    class Meta:
        model = MatingPost
        fields = ['id', 'additional_info', 'existing_pet_id', 'new_pet_data']
        read_only_fields = ['pet']

    def create(self, validated_data):
        existing_pet_id = validated_data.pop('existing_pet_id', None)
        new_pet_data = validated_data.pop('new_pet_data', None)
        user = self.context['request'].user
        pet_instance = None

        if existing_pet_id:
            try:
                pet_instance = Pet.objects.get(id=existing_pet_id, owner=user)
            except Pet.DoesNotExist:
                raise serializers.ValidationError({"existing_pet_id": "Pet does not exist or does not belong to the user."})
        elif new_pet_data:
            pet_instance = Pet.objects.create(owner=user, **new_pet_data)
        
        if pet_instance:
            return MatingPost.objects.create(pet=pet_instance, **validated_data)

        raise serializers.ValidationError("Either 'existing_pet_id' or 'new_pet_data' must be provided.")