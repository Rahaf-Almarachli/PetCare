
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PetViewSet


# إنشاء router تلقائي
router = DefaultRouter()
router.register(r'pets', PetViewSet, basename='pet')

# ربط الـ router بمسارات الـ URL
urlpatterns = [
    path('', include(router.urls)),
    ]