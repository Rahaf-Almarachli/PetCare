from django.urls import path
from .views import RegisterPushTokenView

urlpatterns = [
    # المسار: POST /api/notifications/register/
    path('register/', RegisterPushTokenView.as_view(), name='register_push_token'),
]