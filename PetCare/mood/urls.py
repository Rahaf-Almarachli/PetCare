from django.urls import path
from .views import MoodCreateView, MoodHistoryView

urlpatterns = [
    path('moods/create/', MoodCreateView.as_view(), name='mood-create'),
    path('moods/history/<int:pet_id>/', MoodHistoryView.as_view(), name='mood-history'),
]
