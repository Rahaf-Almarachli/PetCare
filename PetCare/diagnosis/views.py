from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging
import os
import tempfile 
import json
from django.core.files.uploadedfile import InMemoryUploadedFile

# المكتبة الصحيحة: نستخدم مكتبة inference التي تم تثبيتها بنجاح
from inference.http.base_client import InferenceHTTPClient

logger = logging.getLogger(__name__)

class CatDiagnosisView(APIView):
    """
    نقطة نهاية تستخدم InferenceHTTPClient للتشخيص.
    تعتمد على المتغيرات البيئية ROBOFLOW_INFERENCE_URL و ROBOFLOW_API_KEY و ROBOFLOW_MODEL_ID.
    """

    def post(self, request, *args, **kwargs):
        # 1. التحقق من وجود الصورة
        image_file: InMemoryUploadedFile = request.FILES.get('image_file')
        if not image_file:
            return Response(
                {"detail": "Image file is missing..."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. إعداد العميل (Client) باستخدام متغيرات Render
        try:
            client = InferenceHTTPClient(
                api_url=settings.ROBOFLOW_INFERENCE_URL, 
                api_key=settings.ROBOFLOW_API_KEY
            )
            model_id = settings.ROBOFLOW_MODEL_ID
            
        except AttributeError as e:
            logger.error(f"Configuration error: Missing Roboflow setting: {e}")
            return Response(
                {"detail": "Configuration error: Missing Roboflow settings in environment variables."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


        temp_file_path = None
        roboflow_result = None 
        
        try:
            # 3. حفظ الملف المؤقت (ضروري لـ client.infer)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(image_file.read())
                temp_file_path = tmp_file.name

            # 4. إجراء الاستدلال (Inference)
            roboflow_result = client.infer(
                temp_file_path, 
                model_id=model_id,
                confidence=40
            )

        except Exception as e:
            logger.error(f"Roboflow Inference Failed: {e}")
            return Response(
                {"detail": f"Inference Failed. Check API Key or Model ID: {e}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        finally:
            # 5. حذف الملف المؤقت
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        # 6. معالجة النتائج وإرجاعها (الحصول على قاموس من الكائن)
        try:
             roboflow_result_dict = roboflow_result.dict()
        except AttributeError:
             # Fallback to json load if .dict() is not available
             roboflow_result_dict = json.loads(roboflow_result.json())

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


        # 7. تحليل النتائج لإرسال إحداثيات الإطار الكامل (X, Y, Width, Height)
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
            "message": "Diagnosis completed successfully (via inference library).",
            "predictions": diagnosis_results,
            **base_response
        }, status=status.HTTP_200_OK)