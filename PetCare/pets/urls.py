from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PetViewSet

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# إنشاء router تلقائي
router = DefaultRouter()
router.register(r'pets', PetViewSet, basename='pet')

# ربط الـ router بمسارات الـ URL
urlpatterns = [
    path('', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    ]