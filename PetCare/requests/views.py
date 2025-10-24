from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.db import transaction 

from .models import InteractionRequest
from pets.models import Pet 
from adoption.models import AdoptionPost 
from mating.models import MatingPost 
from .serializers import (
    RequestCreateSerializer, 
    RequestDetailSerializer, 
    RequestFullDetailSerializer 
)

# 🟢 استيراد نظام النقاط
from rewards.models import UserPoints, PointsTransaction



# ----------------------------------------------------
# 1. View لعرض قائمة الطلبات (Inbox)
# ----------------------------------------------------
class RequestInboxListView(generics.ListAPIView):
    """
    GET: عرض جميع الطلبات الواردة للمستخدم الحالي (بصفته المالك/المستقبل).
    """
    serializer_class = RequestDetailSerializer 
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = InteractionRequest.objects.filter(
            receiver=user
        ).select_related(
            'sender', 'pet'
        ).order_by('-created_at')
        
        return queryset

# ----------------------------------------------------
# 2. View لعرض تفاصيل الطلب (Detail)
# ----------------------------------------------------
class RequestDetailView(generics.RetrieveAPIView):
    """
    GET: عرض تفاصيل طلب معين.
    """
    serializer_class = RequestFullDetailSerializer 
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        return InteractionRequest.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender', 'pet')

# ----------------------------------------------------
# 3. View لإنشاء طلب جديد
# ----------------------------------------------------
class CreateInteractionRequestView(generics.CreateAPIView):
    """
    POST: إنشاء طلب تفاعل جديد.
    """
    serializer_class = RequestCreateSerializer 
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save()
        # 💥 هنا يتم استخدام Serializer التفصيلي لعرض بيانات المرسل/المستقبل كاملاً
        response_serializer = RequestFullDetailSerializer(instance) 
        return response_serializer.data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        response_data = self.perform_create(serializer)
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class RequestUpdateStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def patch(self, request, id):
        request_obj = get_object_or_404(InteractionRequest, id=id)
        user = request.user

        if request_obj.receiver != user:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        pet = request_obj.pet

        if not new_status or new_status not in ['Accepted', 'Rejected']:
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        request_obj.status = new_status
        request_obj.save(update_fields=['status'])

        if new_status == 'Accepted':
            sender = request_obj.sender
            action_message = ""

            # 🟢 تبنّي
            if request_obj.request_type == 'Adoption':
                pet.owner = sender
                pet.save()
                AdoptionPost.objects.filter(pet=pet).delete()

                # 🏆 أضف النقاط
                points, _ = UserPoints.objects.get_or_create(user=sender)
                points.balance += 100
                points.save()
                PointsTransaction.objects.create(
                    user=sender,
                    event_type="adoption_success",
                    reference=f"adopt:{pet.id}",
                    amount=100
                )
                action_message = "Adoption completed (+100 points)."

            # 🟢 تزاوج
            elif request_obj.request_type == 'Mate':
                MatingPost.objects.filter(pet=pet).delete()

                # 🏆 أضف النقاط
                points, _ = UserPoints.objects.get_or_create(user=sender)
                points.balance += 80
                points.save()
                PointsTransaction.objects.create(
                    user=sender,
                    event_type="mating_success",
                    reference=f"mate:{pet.id}",
                    amount=80
                )
                action_message = "Mating completed (+80 points)."

            InteractionRequest.objects.filter(pet=pet).delete()

            return Response(
                {"detail": f"Request accepted. {action_message}"},
                status=status.HTTP_200_OK
            )

        elif new_status == 'Rejected':
            request_obj.delete()
            return Response({"detail": "Request rejected."}, status=status.HTTP_200_OK)
