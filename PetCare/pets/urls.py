from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PetViewSet, pet_qr_page, user_pets_qr_list

router = DefaultRouter()
# 1. سيقوم الـ Router بتسجيل '/pets/'
router.register(r'pets', PetViewSet, basename='pet')

urlpatterns = [
    # 1. مسارات الـ ViewSet: (pets/, pets/<pk>/)
    path('', include(router.urls)), 
    
    # 2. مسار صفحة الويب العامة:
    # سيتم الوصول إليه عبر: /pets/qr/<token>/ (إذا تم تضمين pets.urls تحت /api/)
    path('pets/qr/<str:token>/', pet_qr_page, name='pet-qr-page'),
    
    # 3. مسار API قائمة الـ QR:
    # سيتم الوصول إليه عبر: /pets/qr-codes/ (إذا تم تضمين pets.urls تحت /api/)
    path('qr-codes/', user_pets_qr_list, name='user-pets-qr-list'), 
]