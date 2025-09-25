# alerts/urls.py
from django.urls import path
from .views import AlertCreateView, AlertUpdateView

urlpatterns = [
    path('alerts/', AlertCreateView.as_view(), name='alert-list-create'),
    path('alerts/<int:pk>/', AlertUpdateView.as_view(), name='alert-update-delete'),
]
