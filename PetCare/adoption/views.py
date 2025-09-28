from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch

# 🛑 الاستيرادات اللازمة (يفضل أن تكون في الأعلى)
from pets.models import Pet
from adoption.models import AdoptionPost
from .serializers import (
    PetAdoptionDetailSerializer, 
    AdoptionPostExistingPetSerializer, 
    NewPetAdoptionSerializer
)
from .filters import AdoptionFilter
# ---------------------------------------------------------------------

class AdoptionListView(generics.ListAPIView):
    """
    GET: عرض قائمة الحيوانات المعروضة للتبني.
    
    الاستعلام يبدأ من نموذج Pet ويتأكد من وجود منشور تبني مرتبط (AdoptionPost).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    # الممارسة القياسية: تعيين الكلاسات مباشرة في الكلاس
    serializer_class = PetAdoptionDetailSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdoptionFilter

    def get_queryset(self):
        # 🛑 الإصلاح الجذري لمشكلة FieldError (AdoptionListView) 🛑
        # 1. الاستعلام يبدأ من Pet (لأن السيريالايزر يتوقع Pet)
        queryset = Pet.objects.filter(
            # 2. التصفية بناءً على وجود العلاقة العكسية (adoption_post)
            # نفترض أن العلاقة العكسية لـ AdoptionPost.pet هي 'adoption_post'
            adoption_post__isnull=False 
        ).select_related(
            'owner' # تحسين الأداء: جلب المالك
        ).prefetch_related(
            'vaccination_set' # تحسين الأداء: جلب اللقاحات
            # لا حاجة لاستخدام Prefetch لـ AdoptionPost لأنه يتم الوصول إليه عبر العلاقة العكسية
        ).order_by('-adoption_post__created_at')
        
        return queryset


class CreateAdoptionPostView(APIView):
    """
    POST: إنشاء منشور تبني جديد.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        
        # تحديد أي سيريالايزر سيتم استخدامه بناءً على البيانات المرسلة
        if 'pet_id' in data:
            # حالة: اختيار حيوان موجود
            serializer_class = AdoptionPostExistingPetSerializer
        elif all(k in data for k in ['pet_name', 'pet_type', 'owner_message']):
            # حالة: إنشاء حيوان جديد ومنشور تبني
            serializer_class = NewPetAdoptionSerializer
        else:
            return Response(
                {"error": "Invalid data"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = serializer_class(data=data, context={'request': request})
        
        if serializer.is_valid():
            # حفظ المنشور والحصول على كائن AdoptionPost (بناءً على التعديلات السابقة)
            adoption_post = serializer.save()
            
            # نحصل على كائن Pet من كائن AdoptionPost لغرض العرض
            response_serializer = PetAdoptionDetailSerializer(adoption_post.pet)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
