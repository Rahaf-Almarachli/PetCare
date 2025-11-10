from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404 
from django.db.models import Prefetch
from django.db import transaction 

from pets.models import Pet
from .models import MatingPost
from .serializers import (
    PetMatingDetailSerializer, 
    MatingPostExistingPetSerializer, 
    NewPetMatingSerializer 
)
from vaccination.models import Vaccination 

# ---------------------------------------------------------------------

class MatingListView(APIView):
    """
    GET: 
    يعرض القائمة الكاملة أو يقوم بالفلترة التلقائية بناءً على target_pet_id.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        target_pet_id = request.query_params.get('target_pet_id')
        
        # لا زلنا نحتاج Prefetch هنا لتحميل البيانات في القائمة بكفاءة
        queryset = Pet.objects.filter(
            mating_post__isnull=False 
        ).select_related(
            'owner'
        ).prefetch_related(
            Prefetch('mating_post', queryset=MatingPost.objects.all()), 
            'vaccinations' 
        ).order_by('-mating_post__created_at')

        selected_pet_name = None
        
        if target_pet_id:
            try:
                target_pet = get_object_or_404(Pet, id=target_pet_id, owner=request.user)
                
                required_gender = None
                if target_pet.pet_gender == 'Male':
                    required_gender = 'Female'
                elif target_pet.pet_gender == 'Female':
                    required_gender = 'Male'
                
                if required_gender:
                    queryset = queryset.filter(
                        pet_gender=required_gender, 
                        pet_type=target_pet.pet_type
                    )
                
                selected_pet_name = target_pet.pet_name
                
            except Pet.DoesNotExist:
                return Response(
                    {"error": "The selected pet was not found or does not belong to the user."}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {"error": f"An unexpected error occurred: {e}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = PetMatingDetailSerializer(queryset, many=True, context={'request': request})
        
        response_data = {
            "target_pet_name": selected_pet_name, 
            "results": serializer.data 
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class CreateMatingPostView(APIView):
    """
    POST: إنشاء منشور تزاوج جديد.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        
        if 'pet_id' in data:
            serializer_class = MatingPostExistingPetSerializer
        elif all(k in data for k in ['pet_name', 'pet_type', 'owner_message', 'pet_birthday', 'pet_gender']):
            serializer_class = NewPetMatingSerializer
        else:
            return Response(
                {"error": "Invalid data format. Missing required fields for new pet or pet_id for existing pet."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = serializer_class(data=data, context={'request': request})
        
        if serializer.is_valid():
            mating_post = serializer.save()
            
            # 🟢 الحل النهائي: جلب كائن Pet المرتبط مع تحميل العلاقات الضرورية (لكن الاعتماد على SerializerMethodField لـ owner_message)
            try:
                pet_to_display = Pet.objects.filter(
                    id=mating_post.pet.id
                ).select_related('owner').prefetch_related(
                    Prefetch('mating_post', queryset=MatingPost.objects.all()), # ابقاء Prefetch كبديل لـ SerializerMethodField
                    'vaccinations' 
                ).first()
            except Exception as e:
                return Response({"error": f"Database query failed after post creation: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if pet_to_display:
                response_serializer = PetMatingDetailSerializer(pet_to_display) 
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "Post created but pet link failed during retrieval."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)