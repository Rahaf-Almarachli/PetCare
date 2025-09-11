import django_filters
from .models import AdoptionPost

class AdoptionPostFilter(django_filters.FilterSet):
    """
    Filter for AdoptionPost model to allow filtering by pet details.
    """
    pet_type = django_filters.CharFilter(
        field_name='pet__pet_type', 
        lookup_expr='iexact'
    )
    pet_gender = django_filters.CharFilter(
        field_name='pet__pet_gender', 
        lookup_expr='iexact'
    )
    pet_color = django_filters.CharFilter(
        field_name='pet__pet_color', 
        lookup_expr='iexact'
    )
    
    class Meta:
        model = AdoptionPost
        fields = ['pet_type', 'pet_gender', 'pet_color']