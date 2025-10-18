from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PetViewSet, PetQRCodeLookupView # 💥 يجب استيراد الـ View الجديد

# إنشاء router تلقائي
router = DefaultRouter()
router.register(r'pets', PetViewSet, basename='pet') 

# ربط الـ router بمسارات الـ URL
urlpatterns = [
    # 💥 المسار المنفصل الخاص بـ API الـ QR code
    # هذا الـ Endpoint هو ما يتم وضعه داخل الـ QR code
    path('qr-lookup/<uuid:qr_token>/', PetQRCodeLookupView.as_view(), name='pet-qr-lookup'),
    
    # مسارات API الحالية (لـ CRUD على الحيوانات الأليفة)
    path('', include(router.urls)),
]
# ⚠️ تم نسيان مسار 'pet-info-detail' (الخاص بالـ HTML) مؤقتاً بناءً على طلبك.