from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RewardListViewSet, UserPointsViewSet, RedeemRewardView

router = DefaultRouter()
router.register(r'list', RewardListViewSet, basename='reward-list')
router.register(r'wallet', UserPointsViewSet, basename='user-wallet') 

urlpatterns = [
    path('', include(router.urls)),
    path('redeem/', RedeemRewardView.as_view(), name='reward-redeem'),
]