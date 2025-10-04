from rest_framework import serializers
from pets.models import Pet
# افترض أن User موجود في account.models
from account.models import User 
from .models import MatingPost
from django.db import transaction

# ----------------------------------------------------
# 1. مُسلسل لعرض الحيوانات المتاحة للتزاوج (MatingListView)
# ----------------------------------------------------
class PetMatingDetailSerializer(serializers.ModelSerializer):
    """
    مُسلسل لعرض تفاصيل الحيوان المعروض للتزاوج (البنية المطلوبة).
    """
    # تسطيح بيانات المالك
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    owner_location = serializers.CharField(source='owner.location', read_only=True)
    
    # جلب رسالة المالك من MatingPost
    owner_message = serializers.CharField(source='mating_post.owner_message', read_only=True)
    
    age = serializers.ReadOnlyField() 
    
    class Meta:
        model = Pet
        fields = [
            'id', 'pet_name', 'pet_type', 'pet_color', 'pet_gender', 
            'age', 'pet_photo', 
            'owner_name',       
            'owner_location',   
            'owner_message', 
        ]

# ----------------------------------------------------
# 2. مُسلسل لإنشاء منشور تزاوج جديد (الحالة 1: اختيار حيوان موجود)
# ----------------------------------------------------
class MatingPostExistingPetSerializer(serializers.ModelSerializer):
    pet_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = MatingPost
        fields = ['pet_id', 'owner_message']
        
    def create(self, validated_data):
        pet_id = validated_data.pop('pet_id')
        user = self.context['request'].user
        
        try:
            # 1. جلب الحيوان والتأكد من أنه ملك للمستخدم
            pet = Pet.objects.get(id=pet_id, owner=user)
        except Pet.DoesNotExist:
            raise serializers.ValidationError({"pet_id": "Pet not found or does not belong to the user."})

        # 🟢 2. التحقق المُصحح: التأكد من عدم وجود منشور تزاوج حالي لهذا الحيوان 🟢
        # نستخدم استعلام قاعدة بيانات للتأكد، بدلاً من التحقق من وجود خاصية على الكائن
        if MatingPost.objects.filter(pet=pet).exists():
            raise serializers.ValidationError({"pet_id": "This pet is already posted for mating."})
            
        # 3. إنشاء منشور التزاوج الجديد
        return MatingPost.objects.create(pet=pet, **validated_data)


# ----------------------------------------------------
# 3. مُسلسل لإنشاء حيوان جديد وعرضه للتزاوج (الحالة 2: Add a new pet)
# ----------------------------------------------------
class NewPetMatingSerializer(serializers.Serializer):
    """
    يستخدم لإنشاء سجل Pet جديد ثم ربطه بمنشور MatingPost جديد.
    """
    # حقول نموذج Pet
    pet_name = serializers.CharField(max_length=100)
    pet_type = serializers.CharField(max_length=50)
    pet_color = serializers.CharField(max_length=50)
    pet_gender = serializers.CharField(max_length=20)
    pet_birthday = serializers.DateField()
    pet_photo = serializers.URLField(required=False, allow_null=True)
    
    # حقل رسالة المالك لنموذج MatingPost
    owner_message = serializers.CharField()
    
    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        
        # 1. إنشاء سجل الحيوان الأليف أولاً
        owner_message = validated_data.pop('owner_message')
        pet_data = validated_data
        
        pet = Pet.objects.create(
            owner=user, 
            **pet_data
        )
        
        # 2. إنشاء منشور التزاوج وربطه بالحيوان الجديد
        mating_post = MatingPost.objects.create(
            pet=pet,
            owner_message=owner_message
        )
        return mating_post
