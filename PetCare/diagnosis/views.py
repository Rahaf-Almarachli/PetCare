from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging
import os
import tempfile 
from django.core.files.uploadedfile import InMemoryUploadedFile

# المكتبة الجديدة: inference_sdk (يجب التأكد من تثبيتها في بيئة Render)
from inference_sdk import InferenceHTTPClient

logger = logging.getLogger(__name__)

class CatDiagnosisView(APIView):
    """
    نقطة نهاية تستخدم مكتبة inference-sdk (وهي الحل الأحدث والأكثر موثوقية)
    لتجاوز أخطاء صلاحيات Workspace.
    """

    def post(self, request, *args, **kwargs):
        # 1. التحقق من وجود الصورة
        image_file: InMemoryUploadedFile = request.FILES.get('image_file')
        if not image_file:
            return Response(
                {"detail": "Image file is missing..."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. إعداد العميل (Client)
        # القيمة التي أرسلتِها: api_key="6vr7QLlL0AJZRrK6fy4vc"
        # القيمة التي أرسلتِها: api_url="https://serverless.roboflow.com"
        
        # نستخدم متغيرات Render البيئية
        try:
            client = InferenceHTTPClient(
                api_url=settings.ROBOFLOW_INFERENCE_URL, # سنضيف هذا المتغير الجديد
                api_key=settings.ROBOFLOW_API_KEY # مفتاحكِ السري
            )
            model_id = settings.ROBOFLOW_MODEL_ID # سنستخدم "skin-disease-of-cat/1" مباشرة
            
        except AttributeError as e:
            logger.error(f"Missing Roboflow setting: {e}")
            return Response(
                {"detail": "Configuration error: Missing Roboflow settings in environment variables."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


        temp_file_path = None
        roboflow_result = None 
        
        try:
            # 3. حفظ الملف المؤقت (ضروري لـ CLIENT.infer)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(image_file.read())
                temp_file_path = tmp_file.name

            # 4. إجراء الاستدلال (Inference) باستخدام المكتبة الجديدة
            # تمرير مسار الملف المحلي و Model ID
            roboflow_result = client.infer(
                temp_file_path, 
                model_id=model_id,
                confidence=40
            )

        except Exception as e:
            logger.error(f"Roboflow Inference Failed (inference-sdk): {e}")
            return Response(
                {"detail": f"Inference Failed. Check API Key or Model ID: {e}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        finally:
            # 5. حذف الملف المؤقت (مهم جداً)
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        # 6. معالجة النتائج وإرجاعها 
        
        # النتائج من InferenceHTTPClient تكون في شكل كائن (object)، نحتاج لتحويله إلى ديكت (dict)
        roboflow_result_dict = roboflow_result.dict()
        
        image_dims = roboflow_result_dict.get('image', {})
        predictions = roboflow_result_dict.get('predictions', [])
        
        
        base_response = {
            "original_width": image_dims.get('width'), 
            "original_height": image_dims.get('height'),
        }

        if not predictions:
             return Response({
                "message": "No specific diseases were detected in the image with high confidence.",
                "predictions": [],
                **base_response
            }, status=status.HTTP_200_OK)


        # تحليل النتائج لعرضها بشكل مُنظم
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
            "message": "Diagnosis completed successfully (via inference-sdk).",
            "predictions": diagnosis_results,
            **base_response
        }, status=status.HTTP_200_OK)