import datetime
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
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
        return Appointment.objects.filter(pet__owner=user)

    def list(self, request, *args, **kwargs):
        """
        Get all appointments for the user, separated into upcoming and past.
        """
        queryset = self.get_queryset()
        now = datetime.date.today()
        
        # تقسيم المواعيد بناءً على التاريخ
        upcoming_appointments = queryset.filter(date__gte=now).order_by('date')
        past_appointments = queryset.filter(date__lt=now).order_by('-date')
        
        # تحويل المجموعات إلى بيانات JSON باستخدام الـ serializer
        upcoming_serializer = self.get_serializer(upcoming_appointments, many=True)
        past_serializer = self.get_serializer(past_appointments, many=True)
        
        return Response({
            'upcoming': upcoming_serializer.data,
            'past': past_serializer.data
        })

    def create(self, request, *args, **kwargs):
        """
        Create a new appointment and return its full details.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # إرجاع بيانات الموعد الكاملة بدلاً من رسالة بسيطة
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """
        Save the new appointment instance.
        """
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single appointment instance.
        """
        instance = get_object_or_404(self.get_queryset(), pk=kwargs['pk'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
