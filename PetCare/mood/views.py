# petcare/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import MoodCreateSerializer
from .models import Mood, Pet
from django.shortcuts import get_object_or_404
from datetime import timedelta, date

class MoodCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MoodCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# View to get mood history
class MoodHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pet_id):
        # التأكد من أن الحيوان الأليف يخص المستخدم المسجل دخوله
        pet = get_object_or_404(Pet, id=pet_id, owner=self.request.user)
        
        # الحصول على سجلات المزاج للأيام السبعة الماضية
        last_seven_days = date.today() - timedelta(days=7)
        moods = Mood.objects.filter(pet=pet, date__gte=last_seven_days).order_by('date')
        
        serializer = MoodCreateSerializer(moods, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)