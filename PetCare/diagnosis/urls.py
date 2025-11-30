# diagnosis/urls.py

from django.urls import path
from .views import CatDiagnosisView

urlpatterns = [
    # الرابط الذي سيستقبل طلبات التشخيص من تطبيق Flutter
    path('cat/', CatDiagnosisView.as_view(), name='cat-diagnosis'),
]