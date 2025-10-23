from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivityViewSet, SystemTriggerViewSet

router = DefaultRouter()
router.register(r'list', ActivityViewSet, basename='activity-list')
router.register(r'', SystemTriggerViewSet, basename='system-trigger') 

urlpatterns = [
    path('', include(router.urls)),
]