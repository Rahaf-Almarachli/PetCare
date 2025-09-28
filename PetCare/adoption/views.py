from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch

# ملاحظة: تم إزالة الاستيرادات لـ serializers, filters, و models من الأعلى
# سنقوم باستيرادها داخل الدوال أو داخل الـ class definition فقط.

# ---------------------------------------------------------------------

class AdoptionListView(generics.ListAPIView):
    """
    GET: عرض قائمة الحيوانات المعروضة للتبني.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    # يجب تعريف هذه الكلاسات باستخدام مسار السلسلة النصية (String Path) 
    # إذا كانت تسبب مشكلة، لكن في DRF الأفضل هو استيرادها محلياً.

    def get_serializer_class(self):
        # الاستيراد داخل الدالة عند الحاجة فقط!
        from .serializers import PetAdoptionDetailSerializer
        return PetAdoptionDetailSerializer
    
    def get_queryset(self):
        # الاستيراد داخل الدالة عند الحاجة فقط!
        from .models import AdoptionPost 
        
        # الاستعلام الأساسي: جلب جميع منشورات التبني النشطة بترتيب زمني عكسي
        queryset = AdoptionPost.objects.select_related('pet', 'pet__owner').prefetch_related(
            Prefetch('pet__vaccinations') 
        ).filter(
            pet__is_available_for_adoption=True
        ).order_by('-created_at')
        
        posts = list(queryset)
        return [post.pet for post in posts]

    # يجب إعادة تعريف هذه الحقول مباشرة في الكلاس باستخدام الاستيراد المحلي
    # (هذا هو المكان الذي كان يحتاج الاستيراد في الأعلى)
    filter_backends = [DjangoFilterBackend]
    
    def get_filterset_class(self):
        from .filters import AdoptionFilter
        return AdoptionFilter


class CreateAdoptionPostView(APIView):
    """
    POST: إنشاء منشور تبني جديد.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # الاستيراد داخل الدالة عند الحاجة فقط!
        from .serializers import AdoptionPostExistingPetSerializer, NewPetAdoptionSerializer, PetAdoptionDetailSerializer
        
        if 'pet_id' in request.data:
            serializer = AdoptionPostExistingPetSerializer(data=request.data, context={'request': request})
        elif 'pet_name' in request.data and 'pet_type' in request.data and 'owner_message' in request.data:
            serializer = NewPetAdoptionSerializer(data=request.data, context={'request': request})
        else:
            return Response({"error": "البيانات المرسلة غير صحيحة."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            adoption_post = serializer.save()
            response_serializer = PetAdoptionDetailSerializer(adoption_post.pet)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
