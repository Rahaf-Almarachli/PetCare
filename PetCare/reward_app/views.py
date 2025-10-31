from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import UserWallet, RewardCoupon
from .serializers import UserWalletSerializer, RedeemRequestSerializer
# 🛑 تم التعديل: استيراد من utils.py في reward_app
from .utils import redeem_points 

# ----------------------------------------------------
# 1. CurrentPointsView 
# ----------------------------------------------------
class CurrentPointsView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserWalletSerializer

    def get_object(self):
        wallet, created = UserWallet.objects.get_or_create(user=self.request.user)
        return wallet
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# ----------------------------------------------------
# 2. RedeemRewardView
# ----------------------------------------------------
class RedeemRewardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RedeemRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reward_system_name = serializer.validated_data['reward_system_name']
        user = request.user

        redeem_result = redeem_points(user, reward_system_name)

        if not redeem_result['success']:
            return Response(
                {"error": redeem_result['message']}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        reward_activity = redeem_result['reward_object']

        # توليد الكوبون
        coupon = RewardCoupon.objects.create(
            user=user,
            reward=reward_activity
        )
        
        return Response(
            {
                "message": redeem_result['message'],
                "coupon_code": str(coupon.code), 
                "reward_name": reward_activity.name,
                "points_cost": reward_activity.points_value,
                "new_points_balance": redeem_result['new_balance']
            }, 
            status=status.HTTP_200_OK
        )