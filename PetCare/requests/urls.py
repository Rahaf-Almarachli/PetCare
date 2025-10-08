from django.urls import path
from .views import (
    CreateInteractionRequestView,
    RequestInboxListView,
    RequestDetailView,
    UpdateRequestStatusView
)

urlpatterns = [
    # 1. POST: Create a new request
    path('create/', CreateInteractionRequestView.as_view(), name='create-interaction-request'),
    
    # 2. GET: List of incoming requests (Inbox)
    path('inbox/', RequestInboxListView.as_view(), name='request-inbox-list'),
    
    # 3. GET: Request details by ID
    path('<int:id>/', RequestDetailView.as_view(), name='request-detail'),
    
    # 4. PATCH: Update request status (Accept/Reject)
    path('<int:id>/status/', UpdateRequestStatusView.as_view(), name='update-request-status'),
]
