from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import MoodCreateSerializer, MoodResponseSerializer, MoodHistorySerializer , LatestMoodSerializer
from .models import Mood
from pets.models import Pet


class MoodCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MoodCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            mood = serializer.save()
            response_serializer = MoodResponseSerializer(mood)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MoodHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pet_id):
        try:
            pet = Pet.objects.get(id=pet_id, owner=self.request.user)
        except Pet.DoesNotExist:
            return Response({"error": "Pet not found or does not belong to the user."},
                            status=status.HTTP_404_NOT_FOUND)
        moods = Mood.objects.filter(pet=pet).order_by('-date')[:7]

        serializer = MoodHistorySerializer(moods, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class LatestMoodView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pet_id):
        try: 
            pet = Pet.objects.get(id=pet_id, owner=self.request.user)
        except Pet.DoesNotExist:
            return Response({"error": "Pet not found or does not belong to the user."},
                            status=status.HTTP_404_NOT_FOUND)

        try:
            latest_mood = Mood.objects.filter(pet=pet).latest('date')
            
        except Mood.DoesNotExist:
            return Response({"message": "No mood entries found for this pet."},
                            status=status.HTTP_404_NOT_FOUND)
        
        serializer = MoodResponseSerializer(latest_mood)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class LatestMoodView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pet_id):
        try:
            pet = Pet.objects.get(id=pet_id, owner=self.request.user)
        except Pet.DoesNotExist:
            return Response({"error": "Pet not found or does not belong to the user."},
                            status=status.HTTP_404_NOT_FOUND)

        try:
            latest_mood = Mood.objects.filter(pet=pet).latest('date')
            
        except Mood.DoesNotExist:
            return Response({"message": "No mood entries found for this pet."},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = LatestMoodSerializer(latest_mood) 
        return Response(serializer.data, status=status.HTTP_200_OK)