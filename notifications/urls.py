from django.urls import path
from .views import RegisterDeviceTokenView

urlpatterns = [
    # API: POST /api/notifications/register-token/
    path('register-token/', RegisterDeviceTokenView.as_view(), name='register-device-token'),
]