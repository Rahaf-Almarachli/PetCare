from rest_framework import viewsets, permissions
from .models import MatingPost
from .serializers import MatingPostSerializer

class MatingPostViewSet(viewsets.ModelViewSet):
    queryset = MatingPost.objects.all()
    serializer_class = MatingPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MatingPost.objects.filter(pet__owner=self.request.user)