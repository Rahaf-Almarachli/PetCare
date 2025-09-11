from rest_framework import viewsets, permissions
from .models import AdoptionPost
from .serializers import AdoptionPostSerializer
from django_filters.rest_framework import DjangoFilterBackend
from .filters import AdoptionPostFilter

class AdoptionPostViewSet(viewsets.ModelViewSet):
    queryset = AdoptionPost.objects.all()
    serializer_class = AdoptionPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_class = AdoptionPostFilter

    def get_queryset(self):
        return AdoptionPost.objects.filter(pet__owner=self.request.user)
