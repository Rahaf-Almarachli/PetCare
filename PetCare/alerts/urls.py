from django.urls import path, include
from rest_framework import routers
from .views import AlertViewSet

router = routers.DefaultRouter()
router.register(r'alerts', AlertViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
