from django.urls import path
from .views import MoodCreateView, MoodHistoryView, LatestMoodView

urlpatterns = [
    path('moods/create/', MoodCreateView.as_view(), name='mood-create'),
    path('moods/history/<int:pet_id>/', MoodHistoryView.as_view(), name='mood-history'),
    path('moods/latest/<int:pet_id>/', LatestMoodView.as_view(), name='mood-latest'),
]

