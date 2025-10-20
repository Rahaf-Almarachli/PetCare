from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PetViewSet, pet_qr_page, user_pets_qr_list

router = DefaultRouter()
router.register(r'pets', PetViewSet, basename='pet')

urlpatterns = [
    path('', include(router.urls)),
    path('pets/qr/<str:token>/', pet_qr_page, name='pet-qr-page'),
    path('pets/qr-codes/', user_pets_qr_list, name='user-pets-qr-list'),
]
