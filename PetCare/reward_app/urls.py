from django.urls import path
from .views import CurrentPointsView, RedeemRewardView

urlpatterns = [
    # المسار سيكون: /reward_app/points/balance/
    path('points/balance/', CurrentPointsView.as_view(), name='current-points'),
    
    # المسار سيكون: /reward_app/points/redeem/
    path('points/redeem/', RedeemRewardView.as_view(), name='redeem-reward'),
]