from django.urls import path
from .views import (
    RewardsSummaryView,
    RewardListView,
    RedeemRewardView,
    MyRedeemedRewardsView
)

urlpatterns = [
    path('summary/', RewardsSummaryView.as_view(), name='rewards-summary'),
    path('available/', RewardListView.as_view(), name='rewards-list'),
    path('redeem/<int:reward_id>/', RedeemRewardView.as_view(), name='redeem-reward'),
    path('my-redeemed/', MyRedeemedRewardsView.as_view(), name='my-redeemed-rewards'),
]
