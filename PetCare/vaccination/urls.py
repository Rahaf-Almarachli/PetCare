from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import VaccinationViewSet
from pets.views import PetViewSet 
from rest_framework_nested import routers

# الموجه الرئيسي للموارد
router = DefaultRouter()
router.register(r'pets', PetViewSet, basename='pet')
# أضف هذا السطر لتسجيل VaccinationsViewSet في الموجه الرئيسي
router.register(r'vaccinations', VaccinationViewSet, basename="vaccination")

# موجه متداخل للموارد الفرعية (التطعيمات)
pets_router = routers.NestedSimpleRouter(router, r'pets', lookup='pet')
pets_router.register(r'vaccinations', VaccinationViewSet, basename='pet-vaccinations')

urlpatterns = [
    # روابط رئيسية مثل /api/pets/ و /api/vaccinations/
    path('', include(router.urls)),
    
    # روابط متداخلة مثل /api/pets/1/vaccinations/
    path('', include(pets_router.urls)),
]