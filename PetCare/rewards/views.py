from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Reward, UserPoints, PointTransaction
from .serializers import RewardSerializer, RedeemSerializer, PointTransactionSerializer
from pets.models import Pet 
from django.contrib.auth import get_user_model

User = get_user_model()

class RewardStatusView(APIView):
    """ يعرض النقاط الحالية، والمكافآت المتاحة، وسجل الكسب. """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        user_points, created = UserPoints.objects.get_or_create(user=user)
        
        # 1. جلب قائمة المكافآت (Redeem Rewards)
        rewards = Reward.objects.filter(is_active=True).order_by('points_required')
        rewards_data = RewardSerializer(rewards, many=True).data

        # 2. قائمة أنشطة الكسب (Earn Points) - يجب أن تكون ثابتة ومحدثة حسب حالة المستخدم
        
        # للتحقق من اكتمال الملف الشخصي، نفترض أن User.location أو User.phone يشيران لذلك
        profile_complete = user.location and user.phone and user.profile_picture

        earn_activities = [
            {"activity": "Complete your profile", "points": 50, 
             "is_completed": bool(profile_complete)},
             
            {"activity": "Adopt a pet", "points": 100, 
             "is_completed": Pet.objects.filter(owner=user).exists()},
             
            {"activity": "Pet Mating", "points": 80, 
             "is_completed": False}, # يجب ربط هذا بنموذج Mating لاحقًا
        ]

        # 3. سجل المعاملات (اختياري)
        transactions = PointTransaction.objects.filter(user=user).order_by('-timestamp')[:5]
        transaction_data = PointTransactionSerializer(transactions, many=True).data

        return Response({
            "total_points": user_points.total_points,
            "rewards_to_redeem": rewards_data,
            "earn_activities": earn_activities,
            "recent_transactions": transaction_data
        }, status=status.HTTP_200_OK)

class RewardRedeemView(APIView):
    """ لمعالجة طلبات استبدال المكافأة. """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RedeemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reward_id = serializer.validated_data['reward_id']

        try:
            reward = Reward.objects.get(id=reward_id, is_active=True)
        except Reward.DoesNotExist:
            return Response({"error": "Reward not found or inactive."}, status=status.HTTP_404_NOT_FOUND)

        user_points = UserPoints.objects.get_or_create(user=request.user)[0]

        if user_points.total_points < reward.points_required:
            return Response({"error": "Insufficient points. You need " + str(reward.points_required - user_points.total_points) + " more points."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # تنفيذ الاستبدال (في معاملة واحدة لضمان الدقة)
        try:
            with transaction.atomic():
                user_points.total_points -= reward.points_required
                user_points.save()

                PointTransaction.objects.create(
                    user=request.user,
                    points_change=-reward.points_required,
                    transaction_type='REDEEM',
                    description=f"Redeemed: {reward.name}"
                )
                
                # 💡 يجب إضافة منطق هنا لربط المكافأة بخدمة مقدم الخدمة (e.g., إنشاء رمز قسيمة)
                
        except Exception:
            return Response({"error": "An error occurred during redemption. Please try again."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": f"Successfully redeemed '{reward.name}'. Your new balance is {user_points.total_points} points.", 
                         "new_points": user_points.total_points}, 
                        status=status.HTTP_200_OK)