from rest_framework import serializers
from .models import Pet

class PetSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Pet
        fields = ['id', 'owner', 'pet_name', 'pet_type', 'pet_color', 'pet_gender', 'pet_birthday', 'pet_photo' , 
                  'age']
        read_only_fields = ['owner']