from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MatingPostViewSet

router = DefaultRouter()
router.register(r'adoption-post', MatingPostViewSet, basename='mating-post')

urlpatterns = [
    path('', include(router.urls)),
]