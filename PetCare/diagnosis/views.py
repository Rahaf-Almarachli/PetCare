from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging
import os
from roboflow import Roboflow # المكتبة الرسمية
import tempfile 
from django.core.files.uploadedfile import InMemoryUploadedFile

logger = logging.getLogger(__name__)

class CatDiagnosisView(APIView):
    """
    نقطة نهاية (Endpoint) لاستقبال صورة وتشخيص أمراض القطط باستخدام Roboflow SDK.
    يجب أن تكون مكتبة 'roboflow' مثبتة في البيئة.
    """

    def post(self, request, *args, **kwargs):
        # 1. التحقق من وجود الصورة
        image_file: InMemoryUploadedFile = request.FILES.get('image_file')
        if not image_file:
            return Response(
                {"detail": "Image file is missing..."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. إعداد مفاتيح Roboflow
        api_key = settings.ROBOFLOW_API_KEY
        model_endpoint = settings.ROBOFLOW_MODEL_ENDPOINT
        
        # فصل معرّف المشروع ورقم الإصدار (مثال: 'maria-angelica-kngdu/skin-disease-of-cat' و '1')
        try:
            # افتراض أن التنسيق هو 'project_name/version'
            project_id, version_id = model_endpoint.rsplit('/', 1) 
        except ValueError:
             return Response(
                {"detail": "ROBOFLOW_MODEL_ENDPOINT format is incorrect. Expected: project_id/version_id"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


        # 3. حفظ الملف المؤقت للاستخدام من قبل SDK
        # يجب استخدام مسار ملف مؤقت لأن SDK لا تتعامل بشكل جيد مع InMemoryUploadedFile مباشرة
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                # كتابة محتوى الصورة إلى الملف المؤقت
                tmp_file.write(image_file.read())
                temp_file_path = tmp_file.name

            # 4. المصادقة والتحميل باستخدام SDK
            rf = Roboflow(api_key=api_key)
            
            # يجب تحديد الـ Workspace بناءً على معرّف المشروع
            workspace = rf.workspace 
            project = workspace.projects().get(project_id) 
            model = project.version(int(version_id)).model

            # 5. إجراء الاستدلال (Inference)
            # استخدام مسار الملف المؤقت
            roboflow_result = model.predict(temp_file_path, confidence=40).json()

        except Exception as e:
            logger.error(f"Roboflow SDK Inference Failed: {e}")
            return Response(
                {"detail": f"Roboflow SDK Inference Failed. Check project ID/Version: {e}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        finally:
            # 6. حذف الملف المؤقت (مهم جداً للنظام)
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        # 7. معالجة النتائج وإرجاعها
        predictions = roboflow_result.get('predictions', [])
        
        diagnosis_results = [
            {
                "disease": p.get('class'),
                "confidence": round(p.get('confidence', 0) * 100, 2),
                "location": f"X: {p.get('x')}, Y: {p.get('y')}"
            }
            for p in predictions
        ]

        return Response({
            "message": "Diagnosis completed successfully (via SDK).",
            "predictions": diagnosis_results,
            "raw_response_id": roboflow_result.get('image', {}).get('id')
        }, status=status.HTTP_200_OK)