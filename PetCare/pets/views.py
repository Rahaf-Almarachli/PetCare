from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Pet
from .serializers import PetSerializer


class PetViewSet(viewsets.ModelViewSet):
    """
    API لإدارة الحيوانات الأليفة الخاصة بالمستخدم
    """
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # عرض الحيوانات الخاصة بالمستخدم الحالي فقط
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # عند إنشاء حيوان جديد، يتم توليد qr_token و qr_url تلقائياً
        pet = serializer.save(owner=self.request.user)
        pet.generate_qr_data()
        pet.save()
        return pet

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pet = self.perform_create(serializer)
        data = PetSerializer(pet, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)


# ==============================
# صفحة الويب التي تظهر بعد مسح QR
# ==============================
def pet_qr_page(request, token):
    """
    صفحة ويب تظهر عند مسح كود الـ QR.
    تعرض بيانات الحيوان وصاحبه.
    """
    pet = get_object_or_404(Pet, qr_token=token)
    context = {
        "pet_name": pet.pet_name,
        "pet_photo": pet.pet_photo,
        "owner_name": f"{pet.owner.first_name} {pet.owner.last_name}",
        "owner_phone": pet.owner.phone if hasattr(pet.owner, 'phone') else "Unavailable",
        "owner_location": pet.owner.location if hasattr(pet.owner, 'location') else "Unavailable",
    }
    return render(request, 'pets/pet_qr_page.html', context)


# ==========================================
# قائمة أكواد QR لحيوانات المستخدم (API جديدة)
# ==========================================
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_pets_qr_list(request):
    """
    Endpoint لإرجاع قائمة الحيوانات الخاصة بالمستخدم الحالي.
    تحتوي على اسم الحيوان، صورته، والرابط الثابت (qr_url).
    """
    pets = Pet.objects.filter(owner=request.user)
    data = []

    for pet in pets:
        data.append({
            "pet_name": pet.pet_name,
            "pet_photo": pet.pet_photo,
            "qr_url": pet.qr_url,
        })

    return Response(data)
