from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Reward, UserPoints, PointTransaction
from .serializers import RewardSerializer, PointTransactionSerializer, RedeemSerializer

class RewardListViewSet(viewsets.ReadOnlyModelViewSet):
    """ واجهة لعرض قائمة المكافآت المتاحة للاستبدال. """
    queryset = Reward.objects.filter(is_active=True).order_by('points_required')
    serializer_class = RewardSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserPointsViewSet(viewsets.ViewSet):
    """ واجهة لعرض رصيد المستخدم وسجل معاملاته. """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='me')
    def get_my_points(self, request):
        """ إرجاع إجمالي نقاط المستخدم الحالي. """
        wallet, created = UserPoints.objects.get_or_create(user=request.user)
        return Response({'total_points': wallet.total_points}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """ إرجاع سجل المعاملات النقطية. """
        transactions = PointTransaction.objects.filter(user=request.user).order_by('-timestamp')
        page = self.paginate_queryset(transactions) # يمكنك إزالة pagination إذا لم تكن تحتاجه
        if page is not None:
            serializer = PointTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PointTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

class RedeemRewardView(views.APIView):
    """ نقطة نهاية POST لمعالجة منطق استبدال المكافأة. """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = RedeemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reward_id = serializer.validated_data['reward_id']

        with transaction.atomic():
            user = request.user
            wallet = get_object_or_404(UserPoints, user=user)
            reward = get_object_or_404(Reward, id=reward_id, is_active=True)

            if wallet.total_points < reward.points_required:
                return Response({'detail': 'Insufficient points to redeem this reward.'}, 
                                status=status.HTTP_400_BAD_REQUEST)

            # 1. خصم النقاط
            wallet.total_points -= reward.points_required
            wallet.save()

            # 2. تسجيل معاملة الاستبدال
            PointTransaction.objects.create(
                user=user,
                points_change=-reward.points_required,
                transaction_type='REDEEM',
                description=f'Redeemed reward: {reward.name}'
            )

            # (هنا يمكن إضافة منطق إرسال تفاصيل المكافأة للمستخدم)

            return Response({
                'detail': f'Successfully redeemed {reward.name}.',
                'points_remaining': wallet.total_points
            }, status=status.HTTP_200_OK)