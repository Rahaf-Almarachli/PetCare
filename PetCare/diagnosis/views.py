from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
import logging
import requests  # المكتبة المطلوبة لإرسال طلبات HTTP
import json

logger = logging.getLogger(__name__)

class CatDiagnosisView(APIView):
    """
    نقطة نهاية تستخدم طلب HTTP خام (Raw Request) مباشرة إلى Roboflow لتجنب أخطاء المكتبات.
    """

    def post(self, request, *args, **kwargs):
        image_file: InMemoryUploadedFile = request.FILES.get('image_file')
        if not image_file:
            return Response(
                {"detail": "Image file is missing..."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 1. إعداد المتغيرات من Render
            api_key = settings.ROBOFLOW_API_KEY
            model_id = settings.ROBOFLOW_MODEL_ID # skin-disease-of-cat/1
            
            # بناء نقطة النهاية (Endpoint URL) مباشرة مع المفتاح
            api_url = f"{settings.ROBOFLOW_INFERENCE_URL}/{model_id}?api_key={api_key}"
            
        except AttributeError as e:
            logger.error(f"Configuration error: Missing Roboflow setting: {e}")
            return Response(
                {"detail": "Configuration error: Missing Roboflow settings in environment variables."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        
        try:
            # 2. إرسال الصورة كطلب POST
            image_file.seek(0) # إعادة ضبط مؤشر الملف
            
            # إرسال الطلب مباشرة إلى Roboflow API
            response = requests.post(
                api_url, 
                data=image_file.read(),
                # هذا هو نوع المحتوى المطلوب لإرسال بيانات الصورة الثنائية
                headers={"Content-Type": "application/x-www-form-urlencoded"} 
            )
            
            # 3. التحقق من حالة الاستجابة
            response.raise_for_status() 
            roboflow_result_dict = response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Roboflow HTTP Error: {e.response.status_code}, Response: {e.response.text}")
            return Response(
                {"detail": f"Roboflow Inference Failed (HTTP). Status: {e.response.status_code}. Details: {e.response.text}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Inference General Error: {e}")
            return Response(
                {"detail": f"General Inference Failed: {e}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


        # 4. معالجة النتائج وإرجاعها (مع الإحداثيات الأربعة المطلوبة)
        image_dims = roboflow_result_dict.get('image', {})
        predictions = roboflow_result_dict.get('predictions', [])
        
        base_response = {
            "original_width": image_dims.get('width'), 
            "original_height": image_dims.get('height'),
            "raw_response_id": image_dims.get('id')
        }

        if not predictions:
             return Response({
                "message": "No specific diseases were detected in the image with high confidence.",
                "predictions": [],
                **base_response
            }, status=status.HTTP_200_OK)


        # تحليل النتائج لإرسال إحداثيات الإطار الكامل (X, Y, Width, Height)
        diagnosis_results = [
            {
                "disease": p.get('class'),
                "confidence": round(p.get('confidence', 0) * 100, 2),
                "location_details": { 
                    "x": p.get('x'),
                    "y": p.get('y'),
                    "width": p.get('width'),
                    "height": p.get('height'),
                }
            }
            for p in predictions
        ]


        return Response({
            "message": "Diagnosis completed successfully (via direct HTTP).",
            "predictions": diagnosis_results,
            **base_response
        }, status=status.HTTP_200_OK)