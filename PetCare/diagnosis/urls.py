
from django.urls import path
from .views import diagnose_by_symptoms, CatDiagnosisView

urlpatterns = [
    # المسار 1: التشخيص المعتمد على الأعراض (النموذج المحلي)
    # يمكن الوصول إليه عبر: [Your Domain]/api/symptoms/
    path('symptoms/', diagnose_by_symptoms, name='diagnosis_by_symptoms'),
    
    # المسار 2: التشخيص المعتمد على الصور (Roboflow)
    # يمكن الوصول إليه عبر: [Your Domain]/api/cat/
    path('cat/', CatDiagnosisView.as_view(), name='cat-diagnosis'),
]