from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend

# الاستيرادات اللازمة
from pets.models import Pet
from .models import MatingPost
from .serializers import (
    PetMatingDetailSerializer, 
    MatingPostExistingPetSerializer, 
    NewPetMatingSerializer
)
from .filters import MatingFilter # 🟢 هذا الفلتر تم تعديله ليتضمن فقط pet_gender 🟢
# ---------------------------------------------------------------------

class MatingListView(generics.ListAPIView):
    """
    GET: عرض قائمة الحيوانات المعروضة للتزاوج.
    تدعم الفلترة فقط بناءً على الجنس (pet_gender).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    serializer_class = PetMatingDetailSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MatingFilter # يستخدم الآن الفلتر المبسط

    def get_queryset(self):
        # الاستعلام يبدأ من Pet ويتأكد من وجود منشور تزاوج مرتبط
        queryset = Pet.objects.filter(
            # التصفية بناءً على وجود العلاقة العكسية (mating_post)
            mating_post__isnull=False 
        ).select_related(
            'owner' # تحسين الأداء: جلب المالك لدعم البيانات في Serializer
        ).order_by('-mating_post__created_at')
        
        return queryset


class CreateMatingPostView(APIView):
    """
    POST: إنشاء منشور تزاوج جديد. (لم يتغير المنطق)
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        
        # تحديد أي سيريالايزر سيتم استخدامه بناءً على البيانات المرسلة
        if 'pet_id' in data:
            # حالة: اختيار حيوان موجود
            serializer_class = MatingPostExistingPetSerializer
        elif all(k in data for k in ['pet_name', 'pet_type', 'owner_message']):
            # حالة: إنشاء حيوان جديد ومنشور تزاوج
            serializer_class = NewPetMatingSerializer
        else:
            return Response(
                {"error": "Invalid data format. Requires 'pet_id' or a new pet's details ('pet_name', 'pet_type', 'owner_message')."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = serializer_class(data=data, context={'request': request})
        
        if serializer.is_valid():
            mating_post = serializer.save()
            
            # نحصل على كائن Pet من كائن MatingPost لغرض العرض في الـ response
            response_serializer = PetMatingDetailSerializer(mating_post.pet)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
