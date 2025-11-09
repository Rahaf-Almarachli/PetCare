from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Q 
from django.shortcuts import get_object_or_404
import logging


from reward_app.utils import award_points 
from activity.models import Activity


from .models import InteractionRequest
from pets.models import Pet 
from adoption.models import AdoptionPost 
from mating.models import MatingPost 
from .serializers import (
    RequestCreateSerializer, 
    RequestDetailSerializer, 
    RequestFullDetailSerializer,
    RequestUpdateSerializer 
)


REQUEST_CREATED_KEY = 'SERVICE_REQUEST_CREATED' 
ADOPTION_APPROVED_KEY = 'ADOPTION_APPROVED'
MATING_APPROVED_KEY = 'MATING_APPROVED'

logger = logging.getLogger(__name__)


class RequestInboxListView(generics.ListAPIView): 
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestDetailSerializer 

    def get_queryset(self):
        user = self.request.user
        return InteractionRequest.objects.filter(receiver=user).order_by('-created_at')


class CreateInteractionRequestView(generics.CreateAPIView): 
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestCreateSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request_instance = serializer.save() 
        
        points_awarded = 0
        current_points = 0
        
        try:
            success, points_awarded = award_points(
                user=request.user, 
                activity_system_name=REQUEST_CREATED_KEY,
                description=f"Interaction request created: {request_instance.id}"
            )
            
            if success:
                user_wallet = getattr(request.user, 'userwallet', None)
                current_points = user_wallet.total_points if user_wallet else 0
        except Exception as e:
            logger.error(f"Failed to award points for creating request: {e}")

        response_serializer = RequestFullDetailSerializer(request_instance)
        
        response_data = {
            "message": "Interaction request created successfully.",
            "request_id": request_instance.id,
            "request_details": response_serializer.data,
            "current_points": current_points,
            "points_awarded_now": points_awarded 
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class RequestDetailView(generics.RetrieveAPIView): 
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestFullDetailSerializer 
        
    def get_queryset(self):
        user = self.request.user
        return InteractionRequest.objects.filter(Q(sender=user) | Q(receiver=user))


class RequestUpdateStatusView(APIView): 
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def patch(self, request, pk):
        request_obj = get_object_or_404(InteractionRequest, id=pk)
        user = request.user
        
        if request_obj.receiver != user:
            return Response(
                {"detail": "You do not have permission to modify this request's status."},
                status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get('status')
        owner_response_message = request.data.get('owner_response_message', None)
        
        if not new_status or new_status not in ['Accepted', 'Rejected']:
            return Response(
                {"detail": "Invalid or missing 'status' field (must be Accepted or Rejected)."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RequestUpdateSerializer(
            request_obj, 
            data={'status': new_status, 'owner_response_message': owner_response_message},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save() 
        
        pet = request_obj.pet
        action_message = ""
        
        if new_status == 'Accepted':
            
            points_awarded = 0
            sender_current_points = 0
            
            if request_obj.request_type == 'Adoption':
                pet.owner = request_obj.sender 
                pet.save()
                
                AdoptionPost.objects.filter(pet=pet).delete()
                action_message = "Ownership transferred, pet removed from adoption list."
                activity_key = ADOPTION_APPROVED_KEY
                
            elif request_obj.request_type == 'Mate':
                MatingPost.objects.filter(pet=pet).delete()
                action_message = "Mating request approved, MatingPost deleted."
                activity_key = MATING_APPROVED_KEY
            else:
                activity_key = None

            if activity_key:
                try:
                    success, points_awarded = award_points(
                        user=request_obj.sender, 
                        activity_system_name=activity_key,
                        description=f"{request_obj.request_type} request accepted."
                    )
                    if success:
                        user_wallet = getattr(request_obj.sender, 'userwallet', None)
                        sender_current_points = user_wallet.total_points if user_wallet else 0
                except Exception as e:
                    logger.error(f"Error awarding points to {request_obj.sender.email}: {e}")

            InteractionRequest.objects.filter(pet=pet).delete()
            
            return Response({
                "detail": f"Request accepted. Pet {pet.id} operation complete. {action_message}",
                "owner_message": owner_response_message,
                "points_awarded_to_sender": points_awarded,
                "sender_current_points": sender_current_points
            }, status=status.HTTP_200_OK)

        elif new_status == 'Rejected':
            
            request_id = request_obj.id
            request_obj.delete()

            return Response(
                {"detail": f"Request {request_id} rejected and deleted from your inbox.",
                 "owner_message": owner_response_message},
                status=status.HTTP_200_OK
            )
        
        else:
            return Response({"detail": "Status updated successfully."}, status=status.HTTP_200_OK)