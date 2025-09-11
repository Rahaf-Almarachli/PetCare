from rest_framework import viewsets, permissions
from .models import Vaccination
from .serializers import VaccinationSerializer

class VaccinationViewSet(viewsets.ModelViewSet):
    queryset = Vaccination.objects.all()
    serializer_class = VaccinationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # يعرض فقط التطعيمات الخاصة بحيوانات المستخدم
        return self.queryset.filter(pet__owner=self.request.user)

    def perform_create(self, serializer):
        # يتأكد أن الحيوان تابع للمستخدم
        pet = serializer.validated_data["pet"]
        if pet.owner != self.request.user:
            raise PermissionError("You can only add vaccinations for your own pets.")
        serializer.save()

