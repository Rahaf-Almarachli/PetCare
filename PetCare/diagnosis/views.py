from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings # لاستخدام المتغيرات من settings.py
import requests
import base64
import json
import logging

logger = logging.getLogger(__name__)

class CatDiagnosisView(APIView):
    """
    نقطة نهاية (Endpoint) لاستقبال صورة وتشخيص أمراض القطط باستخدام Roboflow API.
    """

    def post(self, request, *args, **kwargs):
        # 1. التحقق من وجود الصورة في الطلب
        image_file = request.FILES.get('image_file')
        
        if not image_file:
            return Response(
                {"detail": "Image file is missing. Please send the image under the key 'image_file'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. تحويل الصورة إلى Base64
        try:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error reading and encoding image: {e}")
            return Response(
                {"detail": "Failed to process image file."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 3. إعداد طلب Roboflow
        api_key = settings.ROBOFLOW_API_KEY
        model_endpoint = settings.ROBOFLOW_MODEL_ENDPOINT
        api_url = settings.ROBOFLOW_API_URL

        # ****** التعديل الحاسم هنا: إضافة /predict ******
        full_url = f"{api_url}{model_endpoint}/predict" # <-- تم التعديل
        
        # إعداد البارامترات والبيانات
        params = {'api_key': api_key}
        data = {"image": image_base64}
        
        # 4. إرسال الطلب إلى Roboflow
        try:
            roboflow_response = requests.post(
                full_url, 
                params=params, 
                json=data,
                timeout=30 # مهلة زمنية للطلب (30 ثانية)
            )
            # إذا كانت الاستجابة 405 أو 401، سيتم إطلاق استثناء هنا
            roboflow_response.raise_for_status() 
            
            roboflow_result = roboflow_response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Roboflow API Request Failed: {e}")
            # تم تعديل الرسالة لتكون أكثر دقة الآن
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