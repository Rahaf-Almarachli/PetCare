from django.urls import path
from .views import (
    RequestInboxListView,
    RequestDetailView,
    CreateInteractionRequestView,
    # 🟢 الاسم الصحيح 🟢
    RequestUpdateStatusView, 
)

urlpatterns = [
    # مسار إنشاء طلب جديد
    path('create/', CreateInteractionRequestView.as_view(), name='request-create'),
    
    # مسار قائمة الطلبات (Inbox)
    path('inbox/', RequestInboxListView.as_view(), name='request-inbox-list'),
    
    # مسار عرض التفاصيل
    path('<int:id>/', RequestDetailView.as_view(), name='request-detail'),
    
    # مسار تحديث الحالة (PATCH)
    path('<int:id>/status/', RequestUpdateStatusView.as_view(), name='request-update-status'), 
]