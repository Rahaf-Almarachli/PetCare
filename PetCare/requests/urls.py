from django.urls import path
from .views import (
    RequestInboxListView, 
    RequestDetailView, 
    CreateInteractionRequestView, 
    RequestUpdateStatusView
)

urlpatterns = [
    # GET: عرض جميع الطلبات الواردة للمستخدم (Inbox)
    # مثال: /api/requests/inbox/
    path('inbox/', RequestInboxListView.as_view(), name='request-inbox'),

    # POST: إنشاء طلب جديد (تبني أو تزاوج)
    # مثال: /api/requests/create/
    path('create/', CreateInteractionRequestView.as_view(), name='request-create'),

    # GET: عرض تفاصيل طلب محدد (بواسطة ID)
    # مثال: /api/requests/12/detail/
    path('<int:id>/detail/', RequestDetailView.as_view(), name='request-detail'),

    # PATCH: تحديث حالة الطلب (قبول/رفض)
    # هذا هو الـ Endpoint الحاسم الذي يمنح النقاط.
    # مثال: /api/requests/12/update-status/
    path('<int:id>/update-status/', RequestUpdateStatusView.as_view(), name='request-update-status'),
]
