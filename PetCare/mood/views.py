from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import MoodCreateSerializer, MoodHistorySerializer
from .models import Mood
from pets.models import Pet
from datetime import timedelta, date

class MoodCreateView(APIView):
    """إنشاء سجل مزاج جديد"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MoodCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            mood = serializer.save()
            return Response(MoodHistorySerializer(mood).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MoodHistoryView(APIView):
    """عرض المزاجات لآخر 7 أيام باستخدام اسم الحيوان"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pet_name):
        try:
            pet = Pet.objects.get(pet_name=pet_name, owner=self.request.user)
        except Pet.DoesNotExist:
            return Response({"error": "Pet not found or does not belong to the user."},
                            status=status.HTTP_404_NOT_FOUND)

        last_seven_days = date.today() - timedelta(days=7)
        moods = Mood.objects.filter(
            pet=pet,
            date__gte=last_seven_days
        ).order_by('-date')

        serializer = MoodHistorySerializer(moods, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
