from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch

# الاستيرادات اللازمة
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
    
    # تحديد السيريالايزر وخلفية الفلترة وكلاس الفلتر
    serializer_class = PetAdoptionDetailSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdoptionFilter # 🟢 متوافق مع فلاتر النوع والجنس واللون والموقع (owner__location)

    def get_queryset(self):
        # الاستعلام يبدأ من Pet (لأن السيريالايزر يتوقع Pet)
        queryset = Pet.objects.filter(
            # التصفية بناءً على وجود العلاقة العكسية (adoption_post)
            adoption_post__isnull=False 
        ).select_related(
            # 🟢 تحسين الأداء: جلب المالك (owner) في نفس الاستعلام
            # هذا ضروري ومفيد جداً لفلترة 'owner__location'
            'owner' 
        ).prefetch_related(
            # جلب اللقاحات في استعلام منفصل (للـ Serializer)
            'vaccinations' 
        ).order_by('-adoption_post__created_at')
        
        # عند تطبيق الفلاتر (مثل location=Riyadh)، سيستخدم Django REST Framework
        # كلاس AdoptionFilter لتعديل هذا الـ Queryset قبل عرضه.
        
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
                {"error": "Invalid data format. Requires 'pet_id' or a new pet's details ('pet_name', 'pet_type', 'owner_message')."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = serializer_class(data=data, context={'request': request})
        
        if serializer.is_valid():
            # حفظ المنشور والحصول على كائن AdoptionPost 
            adoption_post = serializer.save()
            
            # نحصل على كائن Pet من كائن AdoptionPost لغرض العرض
            response_serializer = PetAdoptionDetailSerializer(adoption_post.pet)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)