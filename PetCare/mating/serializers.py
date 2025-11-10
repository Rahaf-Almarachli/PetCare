# ---------------------------------------------------------------------
# ملف mating/serializers.py (التعديل النهائي)
# ---------------------------------------------------------------------
from rest_framework import serializers
from pets.models import Pet
from account.models import User 
from mating.models import MatingPost 
from django.db import transaction
from vaccination.models import Vaccination 
# لا نحتاج إلى ObjectDoesNotExist عند استخدام MatingPost.objects.get().
# ----------------------------------------------------
# Vaccination Serializer
# ----------------------------------------------------
class VaccinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vaccination
        fields = ['vacc_name', 'vacc_date', 'vacc_certificate'] 

# ----------------------------------------------------
# Pet Mating Detail Serializer (مع الحل النهائي لـ owner_message)
# ----------------------------------------------------
class PetMatingDetailSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    owner_location = serializers.CharField(source='owner.location', read_only=True)
    age = serializers.ReadOnlyField() 
    vaccinations = VaccinationSerializer(many=True, read_only=True) 
    
    # 🌟 التعديل الحاسم: استخدام SerializerMethodField والبحث المباشر
    owner_message = serializers.SerializerMethodField() 

    class Meta:
        model = Pet
        fields = [
            'id', 'pet_name', 'pet_type', 'pet_color', 'pet_gender', 
            'age', 'pet_photo', 
            'owner_name',
            'owner_location',
            'owner_message', 
            'vaccinations', 
        ]
        
    def get_owner_message(self, pet_obj):
        """
        قراءة الرسالة بالبحث المباشر عن MatingPost المرتبط لتجنب مشكلة null.
        """
        try:
            # البحث المباشر عن MatingPost المرتبط بهذا الحيوان
            mating_post = MatingPost.objects.get(pet=pet_obj)
            return mating_post.owner_message
        except MatingPost.DoesNotExist:
            return None
        except Exception:
             return None


# ----------------------------------------------------
# Mating Post Existing Pet Serializer (كما هو)
# ----------------------------------------------------
class MatingPostExistingPetSerializer(serializers.ModelSerializer):
    pet_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = MatingPost
        fields = ['id', 'pet_id', 'owner_message'] 
        read_only_fields = ['id'] 
        
    def create(self, validated_data):
        pet_id = validated_data.pop('pet_id')
        user = self.context['request'].user
        
        try:
            pet = Pet.objects.get(id=pet_id, owner=user)
        except Pet.DoesNotExist:
            raise serializers.ValidationError({"pet_id": "Pet not found or does not belong to the user."})

        if MatingPost.objects.filter(pet=pet).exists():
            raise serializers.ValidationError({"pet_id": "This pet is already posted for mating."})
            
        return MatingPost.objects.create(pet=pet, **validated_data)


# ----------------------------------------------------
# New Pet Mating Serializer (كما هو)
# ----------------------------------------------------
class NewPetMatingSerializer(serializers.Serializer):
    pet_name = serializers.CharField(max_length=100)
    pet_type = serializers.CharField(max_length=50)
    pet_color = serializers.CharField(max_length=50)
    pet_gender = serializers.CharField(max_length=20)
    pet_birthday = serializers.DateField()
    pet_photo = serializers.URLField(required=False, allow_null=True)
    owner_message = serializers.CharField()
    
    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        owner_message = validated_data.pop('owner_message')
        pet_data = validated_data
        
        pet = Pet.objects.create(
            owner=user, 
            **pet_data
        )
        
        mating_post = MatingPost.objects.create(
            pet=pet,
            owner_message=owner_message
        )
        return mating_post