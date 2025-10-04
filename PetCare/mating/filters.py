import django_filters
from pets.models import Pet
# لا حاجة لاستيراد AdoptionPost هنا


class MatingFilter(django_filters.FilterSet):
    """
    فلتر مبسط لعرض منشورات التزاوج بناءً على جنس الحيوان المطلوب.
    يسمح للمستخدم بفلترة النتائج لرؤية الذكور أو الإناث فقط.
    """
    
    # 🟢 الفلتر الوحيد المتبقي: الجنس 🟢
    pet_gender = django_filters.CharFilter(
        field_name='pet_gender', 
        lookup_expr='iexact' # تطابق دقيق غير حساس لحالة الأحرف
    )
    
    # 🛑 تم حذف pet_type, pet_color, و location 🛑

    class Meta:
        model = Pet 
        fields = ['pet_gender']