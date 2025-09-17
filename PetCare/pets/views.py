from rest_framework import viewsets, permissions
from .models import Pet
from .serializers import PetSerializer

class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # يعرض الحيوانات الأليفة التابعة للمستخدم الحالي فقط
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # يحفظ الحيوان الأليف ويربطه بالمستخدم الحالي
        serializer.save(owner=self.request.user)