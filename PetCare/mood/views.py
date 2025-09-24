from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import MoodCreateSerializer, MoodHistorySerializer
from .models import Mood
from pets.models import Pet
from datetime import timedelta, date

class MoodCreateView(APIView):
    """
    View لإنشاء سجل مزاج جديد لحيوان أليف.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MoodCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MoodHistoryView(APIView):
    """
    View لاسترجاع سجلات المزاج لآخر 7 أيام لحيوان أليف معين.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pet_id):
        # التأكد من أن الحيوان الأليف يخص المستخدم المسجل دخوله
        try:
            pet = Pet.objects.get(id=pet_id, owner=self.request.user)
        except Pet.DoesNotExist:
            return Response({"error": "Pet not found or does not belong to the user."}, status=status.HTTP_404_NOT_FOUND)
        
        # حساب التاريخ قبل 7 أيام
        last_seven_days = date.today() - timedelta(days=7)
        
        # جلب سجلات المزاج للحيوان الأليف لآخر 7 أيام فقط، مع ترتيبها تنازلياً حسب التاريخ
        moods = Mood.objects.filter(pet=pet, date__gte=last_seven_days).order_by('-date')
        
        # استخدام Serializer المخصص للعرض
        serializer = MoodHistorySerializer(moods, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)