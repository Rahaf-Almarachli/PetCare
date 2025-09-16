from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.conf import settings

class ImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        file_obj = request.FILES.get('image')

        if not file_obj:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

        # تخزين الصورة
        filename = default_storage.save(f'uploads/{file_obj.name}', file_obj)

        # عمل URL للصورة
        file_url = default_storage.url(filename)
        full_url = request.build_absolute_uri(file_url)

        return Response({'url': full_url}, status=status.HTTP_201_CREATED)