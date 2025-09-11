from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdoptionPostViewSet

router = DefaultRouter()
router.register(r'adoption-posts', AdoptionPostViewSet, basename='adoption-post')

urlpatterns = [
    path('', include(router.urls)),
]

