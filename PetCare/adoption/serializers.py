from rest_framework import serializers
from pets.models import Pet
from vaccination.models import Vaccination
from adoption.models import AdoptionPost
from django.db import transaction

# مُسلسل لبيانات اللقاح (يستخدم داخل مُسلسل العرض الرئيسي)
class VaccinationSerializer(serializers.ModelSerializer):
    # ملاحظة: تم تعديل أسماء الحقول لتتوافق مع نموذج Vaccination الذي أرسلته (vacc_name, vacc_date)
    class Meta:
        model = Vaccination
        fields = ['vacc_name', 'vacc_date', 'vacc_certificate']

# ----------------------------------------------------
# 1. مُسلسل لعرض الحيوانات المتاحة للمتبني
# ----------------------------------------------------
class PetAdoptionDetailSerializer(serializers.ModelSerializer):
    # جلب الموقع من نموذج المالك (Owner)
    owner_location = serializers.CharField(source='owner.location', read_only=True)
    
    # جلب سجلات اللقاح
    vaccinations = VaccinationSerializer(many=True, read_only=True)
    
    # جلب رسالة المالك من نموذج AdoptionPost المرتبط
    owner_message = serializers.CharField(source='adoption_post.owner_message', read_only=True)
    
    # جلب العمر باستخدام الخاصية property age في نموذج Pet
    age = serializers.ReadOnlyField() 
    
    # جلب صورة الحيوان
    pet_photo = serializers.URLField(read_only=True)

    class Meta:
        model = Pet
        fields = [
            'id', 'pet_name', 'pet_type', 'pet_color', 'pet_gender', 
            'age', 'pet_photo', 'owner_location', 'owner_message', 
            'vaccinations'
        ]

# ----------------------------------------------------
# 2. مُسلسل لإنشاء منشور تبني جديد (الحالة 1: اختيار حيوان موجود)
# ----------------------------------------------------
class AdoptionPostExistingPetSerializer(serializers.ModelSerializer):
    # نطلب معرف الحيوان الأليف ورسالة المالك
    pet_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = AdoptionPost
        fields = ['pet_id', 'owner_message']
        
    def create(self, validated_data):
        pet_id = validated_data.pop('pet_id')
        user = self.context['request'].user
        
        try:
            pet = Pet.objects.get(id=pet_id, owner=user)
        except Pet.DoesNotExist:
            raise serializers.ValidationError({"pet_id": "Pet not found or does not belong to the user."})

        if hasattr(pet, 'adoption_post'):
            raise serializers.ValidationError({"pet_id": "This pet is already posted for adoption."})
            
        # نضمن تحديث حالة الحيوان إلى متاح للتبني
        pet.is_available_for_adoption = True
        pet.save()
            
        return AdoptionPost.objects.create(pet=pet, **validated_data)


# ----------------------------------------------------
# 3. مُسلسل لإنشاء حيوان جديد وعرضه للتبني (الحالة 2: Add a new pet)
# ----------------------------------------------------
class NewPetAdoptionSerializer(serializers.Serializer):
    # حقول نموذج Pet
    pet_name = serializers.CharField(max_length=100)
    pet_type = serializers.CharField(max_length=50)
    pet_color = serializers.CharField(max_length=50)
    pet_gender = serializers.CharField(max_length=20)
    pet_birthday = serializers.DateField()
    pet_photo = serializers.URLField(required=False, allow_null=True)
    
    # حقل رسالة المالك لنموذج AdoptionPost
    owner_message = serializers.CharField()
    
    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        
        # 1. إنشاء سجل الحيوان الأليف أولاً
        pet_data = {k: validated_data[k] for k in validated_data if k != 'owner_message'}
        
        # نضمن أن الحيوان الجديد متاح للتبني افتراضياً
        pet = Pet.objects.create(
            owner=user, 
            is_available_for_adoption=True,
            **pet_data
        )
        
        # 2. إنشاء منشور التبني وربطه بالحيوان الجديد
        adoption_post = AdoptionPost.objects.create(
            pet=pet,
            owner_message=validated_data['owner_message']
        )
        return adoption_post
