import django_filters
# 🛑 تم إصلاح الاستيراد: يتم استيراد Pet من pets.models و AdoptionPost من adoption.models
from pets.models import Pet
from adoption.models import AdoptionPost 


class AdoptionFilter(django_filters.FilterSet):
    # الفلترة بناءً على نوع الحيوان الأليف
    # lookup_expr='iexact' يعني تطابق دقيق غير حساس لحالة الأحرف (مثل "dog" تطابق "Dog")
    pet_type = django_filters.CharFilter(
        field_name='pet_type', 
        lookup_expr='iexact'
    )
    
    # الفلترة بناءً على الجنس
    pet_gender = django_filters.CharFilter(
        field_name='pet_gender', 
        lookup_expr='iexact'
    )
    
    # 🟢 الإضافة المطلوبة: الفلترة بناءً على الموقع
    # lookup_expr='icontains' يسمح بالبحث عن جزء من الكلمة (مثل "Gold" تطابق "Golden")
    location = django_filters.CharFilter(
        field_name='pets__location', 
        lookup_expr='icontains'
    )

    pet_color = django_filters.ChoiceFilter(
        field_name='pet_color', 
        choices=Pet.COLOR_CHOICES, # جلب الخيارات مباشرة من النموذج
        # lookup_expr='exact' هو الافتراضي هنا
    )

    class Meta:
        # الفلتر يعتمد على نموذج Pet
        model = Pet 
        fields = ['pet_type', 'pet_gender', 'pet_color' , 'location'] # 🟢 تم إضافة 'location'