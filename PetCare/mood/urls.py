from django.urls import path
from .views import MoodCreateView, MoodHistoryView

urlpatterns = [
    path('moods/create/', MoodCreateView.as_view(), name='mood-create'),
    path('moods/history/<str:pet_name>/', MoodHistoryView.as_view(), name='mood-history'),
]
