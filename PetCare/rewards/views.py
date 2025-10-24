from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import UserPoints, PointsTransaction, Reward, RedeemedReward
from .serializers import RewardSerializer, RedeemedRewardSerializer

# ✅ عرض ملخص النقاط
class RewardsSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        points, _ = UserPoints.objects.get_or_create(user=user)
        transactions = PointsTransaction.objects.filter(user=user).order_by('-created_at')

        return Response({
            "total_points": points.balance,
            "transactions": [
                {
                    "event_type": t.event_type,
                    "amount": t.amount,
                    "created_at": t.created_at
                } for t in transactions
            ]
        })


# ✅ عرض جميع المكافآت المتاحة
class RewardListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RewardSerializer

    def get_queryset(self):
        return Reward.objects.filter(is_active=True).order_by('points_required')


# ✅ استبدال مكافأة
class RedeemRewardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, reward_id):
        user = request.user
        reward = Reward.objects.filter(id=reward_id, is_active=True).first()

        if not reward:
            return Response({"error": "Reward not found or inactive."}, status=status.HTTP_404_NOT_FOUND)

        points, _ = UserPoints.objects.get_or_create(user=user)

        if points.balance < reward.points_required:
            return Response({"error": "Not enough points."}, status=status.HTTP_400_BAD_REQUEST)

        # خصم النقاط
        points.balance -= reward.points_required
        points.save()

        # سجل العملية
        PointsTransaction.objects.create(
            user=user,
            event_type='reward_redeemed',
            reference=f"reward:{reward.id}",
            amount=-reward.points_required
        )

        redeemed = RedeemedReward.objects.create(user=user, reward=reward)

        return Response({
            "message": f"You redeemed {reward.title} successfully!",
            "remaining_points": points.balance
        }, status=status.HTTP_200_OK)


# ✅ عرض المكافآت التي تم استبدالها
class MyRedeemedRewardsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RedeemedRewardSerializer

    def get_queryset(self):
        return RedeemedReward.objects.filter(user=self.request.user).select_related('reward').order_by('-redeemed_at')
