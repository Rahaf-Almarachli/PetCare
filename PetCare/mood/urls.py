# petcare/urls.py
from django.urls import path
from .views import MoodCreateView, MoodHistoryView

urlpatterns = [
    # ... (باقي المسارات) ...
    path('moods/create/', MoodCreateView.as_view(), name='mood-create'),
    path('pets/<int:pet_id>/mood-history/', MoodHistoryView.as_view(), name='mood-history'),
]