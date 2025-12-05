# diagnosis/urls.py

from django.urls import path
from .views import CatDiagnosisView
from .views import SymptomDiagnosisView

urlpatterns = [
    # الرابط الذي سيستقبل طلبات التشخيص من تطبيق Flutter
    path('cat/', CatDiagnosisView.as_view(), name='cat-diagnosis'),
    path('symptoms/', SymptomDiagnosisView.as_view(), name='symptom-diagnosis'),
]