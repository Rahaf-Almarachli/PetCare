from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Appointment
from .serializers import AppointmentSerializer
from pets.models import Pet
from django.shortcuts import get_object_or_404 # يجب استيرادها

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing appointments.
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return appointments only for the pets owned by the current user,
        with an optional filter for a specific pet.
        """
        user = self.request.user
        
        # 1. فلترة المواعيد الخاصة بحيوانات المستخدم الحالي
        queryset = Appointment.objects.filter(pet__owner=user)
        
        # 2. فلترة إضافية بناءً على معرّف الحيوان الأليف من الـ URL
        pet_id = self.kwargs.get('pet_pk')
        if pet_id:
            # تحقق من أن الحيوان موجود ويملكه المستخدم قبل عرض مواعيده
            get_object_or_404(Pet, id=pet_id, owner=self.request.user)
            queryset = queryset.filter(pet_id=pet_id)
            
        return queryset

    def perform_create(self, serializer):
        """
        Create a new appointment with the correct pet instance.
        """
        serializer.save()