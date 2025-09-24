# petcare/urls.py
from django.urls import path
from .views import MoodCreateView, MoodHistoryView

urlpatterns = [
    path('moods/', MoodCreateView.as_view(), name='mood_create'),
    path('moods/<int:pet_id>/history/', MoodHistoryView.as_view(), name='mood_history'),
]