from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Pet
from .serializers import PetSerializer
from django.shortcuts import get_object_or_404 
from django.template.loader import render_to_string 
from django.http import HttpResponse 

class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
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

def pet_qr_page(request, token):
    pet = get_object_or_404(Pet, qr_token=token)
    context = {
        "pet_name": pet.pet_name,
        "pet_photo": pet.pet_photo,
        "owner_name": f"{pet.owner.first_name} {pet.owner.last_name}",
        "owner_phone": pet.owner.phone if hasattr(pet.owner, 'phone') else "Unavailable",
        "owner_location": pet.owner.location if hasattr(pet.owner, 'location') else "Unavailable",
    }

    html_content = render_to_string('pets/pet_qr_page.html', context, request)
    return HttpResponse(html_content, content_type='text/html; charset=utf-8')

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_pets_qr_list(request):
    pets = Pet.objects.filter(owner=request.user)
    data = []

    for pet in pets:
        data.append({
            "pet_name": pet.pet_name,
            "pet_photo": pet.pet_photo,
            "qr_url": pet.qr_url,
        })

    return Response(data)
