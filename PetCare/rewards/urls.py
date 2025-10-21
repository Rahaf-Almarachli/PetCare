from django.urls import path
from .views import RewardStatusView, RewardRedeemView

urlpatterns = [
    path('rewards/status/', RewardStatusView.as_view(), name='reward-status'),
    path('rewards/redeem/', RewardRedeemView.as_view(), name='reward-redeem'),
]