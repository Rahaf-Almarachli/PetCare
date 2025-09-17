import datetime
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Appointment
from .serializers import AppointmentSerializer
from pets.models import Pet
from django.shortcuts import get_object_or_404

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
        
        # فلترة المواعيد الخاصة بحيوانات المستخدم الحالي
        queryset = Appointment.objects.filter(pet__owner=user)
        
        # فلترة إضافية بناءً على معرّف الحيوان الأليف من الـ URL
        pet_id = self.kwargs.get('pet_pk')
        if pet_id:
            # تحقق من أن الحيوان موجود ويملكه المستخدم قبل عرض مواعيده
            get_object_or_404(Pet, id=pet_id, owner=self.request.user)
            queryset = queryset.filter(pet_id=pet_id)
            
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Get all appointments for the user, separated into upcoming and past.
        """
        # استخدام دالة get_queryset لجلب جميع المواعيد الخاصة بالمستخدم الحالي
        queryset = self.get_queryset()
        
        now = datetime.date.today()
        
        # تقسيم المواعيد بناءً على التاريخ
        upcoming_appointments = queryset.filter(date__gte=now).order_by('date')
        past_appointments = queryset.filter(date__lt=now).order_by('-date')
        
        # تحويل المجموعات إلى صيغة JSON باستخدام الـ serializer
        upcoming_serializer = self.get_serializer(upcoming_appointments, many=True)
        past_serializer = self.get_serializer(past_appointments, many=True)
        
        # إرجاع استجابة JSON تحتوي على كلا القائمتين
        return Response({
            'upcoming': upcoming_serializer.data,
            'past': past_serializer.data
        })

    def perform_create(self, serializer):
        """
        Create a new appointment with the correct pet instance.
        """
        serializer.save()