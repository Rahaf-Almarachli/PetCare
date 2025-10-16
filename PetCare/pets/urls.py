from django.urls import path, include
from rest_framework.routers import DefaultRouter
# 💥 يجب استيراد الـ View المخصص لصفحة معلومات الحيوان الأليف
from .views import PetViewSet, pet_info_view 

# إنشاء router تلقائي
router = DefaultRouter()
# تأكد من استخدام basename إذا كان هناك تعارض أو لم يتم تعريف queryset بشكل صحيح
router.register(r'pets', PetViewSet, basename='pet') 

# ربط الـ router بمسارات الـ URL
urlpatterns = [
    # 💥 المسار الخاص بصفحة معلومات الحيوان الأليف (الذي يتم تضمينه في QR Code)
    # يستخدم UUID في الرابط ويشير إلى الدالة pet_info_view
    path('pet-info/<uuid:token>/', pet_info_view, name='pet-info-detail'), 
    
    # مسارات API الحالية (لـ CRUD على الحيوانات الأليفة)
    path('', include(router.urls)),
]