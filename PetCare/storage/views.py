from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
# from django.core.files.storage import default_storage # لم نعد نحتاجها
# from django.conf import settings # لم نعد نحتاجها

# 💥 الإضافة الجديدة
import cloudinary.uploader 

class ImageUploadView(APIView):
    # تسمح باستقبال ملفات متعددة (MultiPart) وبيانات فورمة (Form)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        # ⚠️ ملاحظة: يجب أن ترسل صديقتك الملف باسم 'image' من Flutter
        file_obj = request.FILES.get('image')

        if not file_obj:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 💥 رفع الصورة مباشرة إلى Cloudinary
            # 'pet-care-uploads' هو اسم المجلد في Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_obj, 
                folder="pet-care-uploads" 
            )
            
            # استخراج الرابط الآمن (HTTPS)
            file_url = upload_result.get('secure_url')
            
            # إذا كنت تحتاج المعرف العام (Public ID) أيضاً:
            # public_id = upload_result.get('public_id')

            return Response({'url': file_url}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': f'Cloudinary upload failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)