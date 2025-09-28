import django_filters
# 🛑 تم إصلاح الاستيراد: يتم استيراد Pet من pets.models و AdoptionPost من adoption.models
from pets.models import Pet
from adoption.models import AdoptionPost 


class AdoptionFilter(django_filters.FilterSet):
    # مثال على فلترة بناءً على نوع الحيوان الأليف
    pet_type = django_filters.CharFilter(
        field_name='pet_type', 
        lookup_expr='iexact'
    )
    
    # مثال على فلترة بناءً على الجنس
    pet_gender = django_filters.CharFilter(
        field_name='pet_gender', 
        lookup_expr='iexact'
    )
    
    # يمكنك إضافة المزيد من الفلاتر هنا...

    class Meta:
        # الفلتر يعتمد على نموذج Pet لأن AdoptionListView يرجع كائنات Pet
        model = Pet 
        fields = ['pet_type', 'pet_gender']
