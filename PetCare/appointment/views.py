from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Appointment
from .serializers import AppointmentSerializer
from pets.models import Pet

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing appointments.
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return appointments only for the pets owned by the current user.
        """
        user = self.request.user
        # جلب جميع الحيوانات الأليفة التي يملكها المستخدم الحالي
        user_pets = Pet.objects.filter(owner=user)
        # فلترة المواعيد بناءً على هذه الحيوانات الأليفة
        return Appointment.objects.filter(pet__in=user_pets)

    def perform_create(self, serializer):
        """
        Create a new appointment with the correct pet instance.
        """
        # الـ Serializer already handles the pet validation,
        # so we just need to save the instance.
        serializer.save()
