from django.urls import path
from .views import AdoptionListView, CreateAdoptionPostView

urlpatterns = [
    # API لعرض جميع الحيوانات المتاحة للتبني
    path('adoptions/', AdoptionListView.as_view(), name='adoption-list'),
    
    # API لإنشاء منشور تبني جديد (سواء لحيوان موجود أو جديد)
    path('adoptions/create/', CreateAdoptionPostView.as_view(), name='adoption-create'),
]