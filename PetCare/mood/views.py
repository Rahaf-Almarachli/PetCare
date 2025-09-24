from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import MoodCreateSerializer, MoodResponseSerializer
from .models import Mood
from pets.models import Pet
from datetime import timedelta, date
from django.shortcuts import get_object_or_404

class MoodCreateView(APIView):
    """إنشاء سجل مزاج جديد"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MoodCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            mood = serializer.save()
            response_serializer = MoodResponseSerializer(mood)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MoodHistoryView(APIView):
    """عرض المزاجات لآخر 7 أيام باستخدام id الحيوان"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pet_id):
        # تحقق من ملكية الحيوان
        pet = get_object_or_404(Pet, id=pet_id, owner=self.request.user)

        last_seven_days = date.today() - timedelta(days=7)
        moods = Mood.objects.filter(
            pet=pet,
            date__gte=last_seven_days
        ).order_by('-date')

        serializer = MoodResponseSerializer(moods, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
