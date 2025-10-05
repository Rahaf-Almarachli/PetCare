from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404 

# الاستيرادات اللازمة
from pets.models import Pet
from .models import MatingPost
from .serializers import (
    PetMatingDetailSerializer, 
    MatingPostExistingPetSerializer, 
    NewPetMatingSerializer
)
# ---------------------------------------------------------------------

class MatingListView(APIView):
    """
    GET: 
    1. يعرض القائمة الكاملة (إذا لم يتم إرسال target_pet_id).
    2. يقوم بالفلترة التلقائية للجنس المعاكس ونوع الحيوان (إذا تم إرسال target_pet_id).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # 1. جلب ID الحيوان الأليف من Query Parameters
        target_pet_id = request.query_params.get('target_pet_id')
        
        # 2. الاستعلام الأساسي: جلب جميع الحيوانات المعروضة للتزاوج
        queryset = Pet.objects.filter(
            mating_post__isnull=False 
        ).select_related(
            'owner'
        ).order_by('-mating_post__created_at')

        selected_pet_name = None
        
        if target_pet_id:
            try:
                # جلب الحيوان الأليف الذي اختاره المستخدم (يجب أن يكون مالكاً له)
                target_pet = get_object_or_404(Pet, id=target_pet_id, owner=request.user)
                
                # تحديد الجنس المعاكس للفلترة
                if target_pet.pet_gender == 'Male':
                    required_gender = 'Female'
                elif target_pet.pet_gender == 'Female':
                    required_gender = 'Male'
                else:
                    # في حال كان الجنس غير محدد أو قيمة غير متوقعة
                    required_gender = None 
                
                # 🟢 تطبيق الفلترة التلقائية: الجنس المعاكس ونوع الحيوان 🟢
                if required_gender:
                    queryset = queryset.filter(
                        pet_gender=required_gender, 
                        pet_type=target_pet.pet_type
                    )
                
                # إعداد اسم الحيوان الأليف المُختار لإرجاعه في الاستجابة
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

        # 3. تسلسل البيانات وإرجاع الـ Response بالصيغة المطلوبة
        serializer = PetMatingDetailSerializer(queryset, many=True, context={'request': request})
        
        response_data = {
            "target_pet_name": selected_pet_name, # اسم الحيوان الأليف المُختار (سيكون None في حالة عدم إرسال ID)
            "results": serializer.data             # قائمة الحيوانات المفلترة/الكاملة
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class CreateMatingPostView(APIView):
    """
    POST: إنشاء منشور تزاوج جديد. (لا تغيير هنا)
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        
        # تحديد أي سيريالايزر سيتم استخدامه بناءً على البيانات المرسلة
        if 'pet_id' in data:
            # حالة: اختيار حيوان موجود 
            serializer_class = MatingPostExistingPetSerializer
        elif all(k in data for k in ['pet_name', 'pet_type', 'owner_message', 'pet_birthday', 'pet_gender']):
            # حالة: إنشاء حيوان جديد ومنشور تزاوج
            serializer_class = NewPetMatingSerializer
        else:
            return Response(
                {"error": "Invalid data format. Missing required fields for new pet or pet_id for existing pet."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = serializer_class(data=data, context={'request': request})
        
        if serializer.is_valid():
            mating_post = serializer.save()
            
            # نحصل على كائن Pet من كائن MatingPost لغرض العرض في الـ response
            response_serializer = PetMatingDetailSerializer(mating_post.pet)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)