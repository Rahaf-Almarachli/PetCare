from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import requests
import base64
import json
import logging
from django.core.files.uploadedfile import InMemoryUploadedFile

logger = logging.getLogger(__name__)

class CatDiagnosisView(APIView):
    """
    نقطة نهاية (Endpoint) لاستقبال صورة وتشخيص أمراض القطط باستخدام Roboflow API.
    يستخدم طريقة المصادقة عبر Bearer Token في Headers.
    """

    def post(self, request, *args, **kwargs):
        # 1. التحقق من وجود الصورة في الطلب
        image_file: InMemoryUploadedFile = request.FILES.get('image_file')
        
        if not image_file:
            return Response(
                {"detail": "Image file is missing. Please send the image under the key 'image_file'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. تحويل الصورة إلى Base64
        try:
            # قراءة المحتوى ثم تشفيره
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error reading and encoding image: {e}")
            return Response(
                {"detail": "Failed to process image file."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 3. إعداد طلب Roboflow: استخدام هيدر Authorization وحذف /predict
        api_key = settings.ROBOFLOW_API_KEY
        model_endpoint = settings.ROBOFLOW_MODEL_ENDPOINT
        api_url = settings.ROBOFLOW_API_URL

        # بناء عنوان URL الكامل للنموذج (بدون /predict) <--- التعديل الحاسم هنا
        full_url = f"{api_url}{model_endpoint}" 
        
        # البيانات: نغلف Base64 فقط داخل كائن JSON
        data = {"image": image_base64} 
        
        # استخدام الهيدر Authorization (Bearer Token)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}' 
        }
        
        # 4. إرسال الطلب إلى Roboflow
        try:
            roboflow_response = requests.post(
                full_url, 
                json=data, 
                headers=headers, # <--- إرسال الهيدرات
                timeout=30 
            )
            
            roboflow_response.raise_for_status()
            
            roboflow_result = roboflow_response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Roboflow API Request Failed: {e}")
            return Response(
                {"detail": "Error communicating with the diagnosis service. Please check your Roboflow API configuration and logs."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # 5. معالجة النتائج وإرجاعها إلى العميل
        predictions = roboflow_result.get('predictions', [])
        
        if not predictions:
             return Response({
                "message": "No specific diseases were detected in the image with high confidence.",
                "predictions": []
            }, status=status.HTTP_200_OK)


        # تحليل النتائج لعرضها بشكل مُنظم
        diagnosis_results = [
            {
                "disease": p.get('class'),
                "confidence": round(p.get('confidence', 0) * 100, 2),
                "location": f"X: {p.get('x')}, Y: {p.get('y')}"
            }
            for p in predictions
        ]

        return Response({
            "message": "Diagnosis completed successfully.",
            "predictions": diagnosis_results,
            "raw_response_id": roboflow_result.get('image', {}).get('id')
        }, status=status.HTTP_200_OK)