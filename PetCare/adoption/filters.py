import django_filters
from pets.models import AdoptionPost, Pet
# لا نحتاج Q هنا لأن django_filters يتعامل معها تلقائياً

class AdoptionFilter(django_filters.FilterSet):
    """
    فئة فلترة مخصصة للحيوانات المعروضة للتبني.
    """
    
    # 1. فلترة الموقع: تستخدم CharFilter للبحث النصي (كتابة حرة)
    location = django_filters.CharFilter(
        # المسار للوصول إلى الموقع في نموذج المالك (owner)
        field_name='pet__owner__location', 
        # تعبير البحث: icontains (يحتوي على, غير حساس لحالة الأحرف)
        lookup_expr='icontains',
        label="Location (Search Text)" 
    )

    # 2. فلترة النوع (مطابقة تامة، عادة من قائمة منسدلة)
    pet_type = django_filters.CharFilter(
        field_name='pet__pet_type', 
        lookup_expr='exact',
        label="Pet Type"
    )
    
    # 3. فلترة اللون (مطابقة تامة، عادة من قائمة منسدلة)
    pet_color = django_filters.CharFilter(
        field_name='pet__pet_color', 
        lookup_expr='exact',
        label="Pet Color"
    )
    
    # 4. فلترة الجنس (مطابقة تامة، عادة من قائمة منسدلة)
    pet_gender = django_filters.CharFilter(
        field_name='pet__pet_gender', 
        lookup_expr='exact',
        label="Pet Gender"
    )

    class Meta:
        model = AdoptionPost
        # يتم استخدام الحقول كـ Query Parameters في الـ URL
        fields = ['pet_type', 'pet_color', 'pet_gender', 'location']
