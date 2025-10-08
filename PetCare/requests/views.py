from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser 
from rest_framework.response import Response
from django.db.models import Q
from .serializers import InteractionRequestSerializer, RequestDetailSerializer
from .models import InteractionRequest

class CreateInteractionRequestView(generics.CreateAPIView):
    """ 
    POST /api/requests/create/
    Creates a new Mating/Adoption request, allowing file attachments.
    """
    queryset = InteractionRequest.objects.all()
    serializer_class = InteractionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser) 


class RequestInboxListView(generics.ListAPIView):
    """ 
    GET /api/requests/inbox/
    Lists all incoming requests where the current user is the pet owner (receiver).
    """
    serializer_class = InteractionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter requests where the current user is the intended receiver
        return InteractionRequest.objects.filter(receiver=self.request.user).order_by('-created_at')


class RequestDetailView(generics.RetrieveAPIView):
    """ 
    GET /api/requests/<id>/
    Retrieves the full details of a single request.
    """
    queryset = InteractionRequest.objects.all()
    serializer_class = RequestDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        # Only allow the sender OR the receiver (owner) to view the details
        user = self.request.user
        return InteractionRequest.objects.filter(Q(sender=user) | Q(receiver=user))


class UpdateRequestStatusView(generics.UpdateAPIView):
    """ 
    PATCH /api/requests/<id>/status/
    Used to Accept or Reject a request by updating its status field.
    """
    queryset = InteractionRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['patch']
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # 1. Authorization: Only the receiver (pet owner) can change the status
        if instance.receiver != request.user:
            return Response(
                {"detail": "You are not authorized to change the status of this request."}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        new_status = request.data.get('status')
        valid_statuses = ['Accepted', 'Rejected']

        # 2. Validation
        if new_status not in valid_statuses:
            return Response(
                {"detail": "Invalid status value. Must be 'Accepted' or 'Rejected'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Update Status
        instance.status = new_status
        instance.save()
        
        # --- NOTIFICATION HOOK: Notify the sender that the status changed ---
        
        # Return the updated details
        serializer = RequestDetailSerializer(instance)
        return Response(serializer.data)
