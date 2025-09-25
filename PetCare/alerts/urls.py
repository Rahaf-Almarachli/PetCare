# alerts/urls.py
from django.urls import path
from .views import AlertCreateListView, AlertUpdateDeleteView

urlpatterns = [
    path('alerts/', AlertCreateListView.as_view(), name='alert-list-create'),
    path('alerts/<int:pk>/', AlertUpdateDeleteView.as_view(), name='alert-update-delete'),
]
