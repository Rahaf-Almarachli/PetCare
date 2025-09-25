# alerts/views.py
from rest_framework import generics, permissions
from .models import Alert
from .serializers import AlertSerializer


class AlertCreateListView(generics.ListCreateAPIView):
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(owner=self.request.user)


class AlertUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(owner=self.request.user)
