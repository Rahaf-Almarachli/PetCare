from django.urls import path
from .views import MatingListView, CreateMatingPostView

# يجب إضافة هذا المسار (urls) إلى ملف project/urls.py باستخدام:
# path('api/mating/', include('mating.urls')),

urlpatterns = [
    # GET: عرض قائمة الحيوانات المتاحة للتزاوج (MatingListView)
    # يمكن استخدام الفلترة هنا: .../api/mating/?pet_gender=Male
    path('', MatingListView.as_view(), name='mating-list'),
    
    # POST: إنشاء منشور تزاوج جديد (CreateMatingPostView)
    path('create/', CreateMatingPostView.as_view(), name='create-mating-post'),
]
