import django_filters
# 🛑 تم إصلاح الاستيراد: يتم استيراد Pet من pets.models و AdoptionPost من adoption.models
from pets.models import Pet
from adoption.models import AdoptionPost 


class AdoptionFilter(django_filters.FilterSet):
    # الفلترة بناءً على نوع الحيوان الأليف
    pet_type = django_filters.CharFilter(
        field_name='pet_type', 
        lookup_expr='iexact'
    )
    
    # الفلترة بناءً على الجنس
    pet_gender = django_filters.CharFilter(
        field_name='pet_gender', 
        lookup_expr='iexact'
    )
    
    # 🟢 فلتر اللون: يستخدم ChoiceFilter لضمان صحة القيمة
    pet_color = django_filters.ChoiceFilter(
        field_name='pet_color', 
        choices=Pet.COLOR_CHOICES, # جلب الخيارات مباشرة من النموذج
    )
    
    # 🟢 تصحيح فلتر الموقع 🟢
    # المسار الصحيح: owner (اسم حقل المفتاح الخارجي) __ location (اسم الحقل في نموذج User)
    location = django_filters.CharFilter(
        field_name='owner__location', 
        lookup_expr='icontains' # بحث نصي غير حساس لحالة الأحرف
    )

    class Meta:
        # الفلتر يعتمد على نموذج Pet
        model = Pet 
        fields = ['pet_type', 'pet_gender', 'pet_color' , 'location'] 
