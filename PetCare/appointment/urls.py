from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

# تأكد من استيراد AppointmentViewSet من المسار الحالي
from .views import AppointmentViewSet
# تأكد من استيراد PetViewSet من مساره الصحيح في تطبيق 'pets'
from pets.views import PetViewSet 

# الموجه الرئيسي للموارد
router = DefaultRouter()
# يجب تسجيل PetViewSet هنا أولاً لأنه المورد الأب
router.register(r'pets', PetViewSet, basename='pet')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

# الموجه المتداخل للموارد الفرعية (appointments)
pets_router = routers.NestedSimpleRouter(router, r'pets', lookup='pet')
pets_router.register(r'appointments', AppointmentViewSet, basename='pet-appointments')

urlpatterns = [
    # روابط المستوى الأعلى مثل /api/pets/ و /api/appointments/
    path('', include(router.urls)),
    
    # روابط متداخلة مثل /api/pets/1/appointments/
    path('', include(pets_router.urls)),
]
