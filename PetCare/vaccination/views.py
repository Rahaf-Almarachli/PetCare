from rest_framework import viewsets, permissions
from .models import Vaccination
from .serializers import VaccinationSerializer
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from pets.models import Pet  # يجب استيراد نموذج الحيوان الأليف

class VaccinationViewSet(viewsets.ModelViewSet):
    serializer_class = VaccinationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # يعرض فقط التطعيمات الخاصة بحيوانات المستخدم
        queryset = Vaccination.objects.filter(pet__owner=self.request.user)
        
        # 1. فلترة إضافية بناءً على معرّف الحيوان الأليف من الـ URL
        pet_id = self.kwargs.get('pet_pk')
        if pet_id:
            # 2. تحقق من أن الحيوان موجود ويملكه المستخدم قبل عرض لقاحاته
            get_object_or_404(Pet, id=pet_id, owner=self.request.user)
            queryset = queryset.filter(pet_id=pet_id)
            
        return queryset

    def perform_create(self, serializer):
        # 1. الحصول على كائن الحيوان الأليف من الرابط
        pet_id = self.kwargs.get('pet_pk')
        
        # 2. استخدام get_object_or_404 لضمان وجود الحيوان وملكيتة
        #    هذه الدالة ترجع 404 إذا كان الحيوان غير موجود أو لا ينتمي للمستخدم
        pet = get_object_or_404(Pet, id=pet_id, owner=self.request.user)
            
        # 3. حفظ التطعيم الجديد وربطه بالحيوان
        serializer.save(pet=pet)