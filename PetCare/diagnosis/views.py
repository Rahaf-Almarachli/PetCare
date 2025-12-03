from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging
import os
from roboflow import Roboflow
import tempfile 
from django.core.files.uploadedfile import InMemoryUploadedFile

logger = logging.getLogger(__name__)

class CatDiagnosisView(APIView):
    """
    نقطة نهاية (Endpoint) تستخدم Roboflow SDK للتشخيص.
    تُرجع الأبعاد الأصلية للصورة (original_width/height) لمساعدة تطبيق Flutter في رسم الإطارات.
    """

    def post(self, request, *args, **kwargs):
        # 1. التحقق من وجود الصورة
        image_file: InMemoryUploadedFile = request.FILES.get('image_file')
        if not image_file:
            return Response(
                {"detail": "Image file is missing. Please send the image under the key 'image_file'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. إعداد مفاتيح Roboflow وفصل معرّفات المشروع والإصدار
        api_key = settings.ROBOFLOW_API_KEY
        model_endpoint = settings.ROBOFLOW_MODEL_ENDPOINT
        
        try:
            # مثال: 'maria-angelica-kngdu/skin-disease-of-cat/1'
            project_path, version_id = model_endpoint.rsplit('/', 1)
            # استخراج اسم مساحة العمل (Workspace) واسم المشروع (Slug)
            workspace_name, project_slug = project_path.split('/', 1) 
        except ValueError:
             return Response(
                {"detail": "ROBOFLOW_MODEL_ENDPOINT format is incorrect. Expected: workspace_name/project_name/version_id"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        temp_file_path = None
        roboflow_result = None 
        
        try:
            # 3. حفظ الملف المؤقت للاستخدام من قبل SDK
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(image_file.read())
                temp_file_path = tmp_file.name

            # 4. المصادقة والتحميل باستخدام SDK (التصحيحات)
            rf = Roboflow(api_key=api_key)
            
            # تحديد مساحة العمل باستخدام اسمها الصحيح
            workspace = rf.workspace(workspace_name) 
            project = workspace.project(project_slug) 
            
            model = project.version(int(version_id)).model

            # 5. إجراء الاستدلال (Inference)
            roboflow_result = model.predict(temp_file_path, confidence=40).json()

        except Exception as e:
            logger.error(f"Roboflow SDK Inference Failed: {e}")
            return Response(
                {"detail": f"Roboflow SDK Inference Failed. Check project/version/permissions: {e}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        finally:
            # 6. حذف الملف المؤقت (مهم جداً)
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        # 7. معالجة النتائج وإرجاعها (بما في ذلك الأبعاد الأصلية)
        
        image_dims = roboflow_result.get('image', {}) if roboflow_result else {}
        predictions = roboflow_result.get('predictions', []) if roboflow_result else []
        
        
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


        # تحليل النتائج لعرضها بشكل مُنظم
        diagnosis_results = [
            {
                "disease": p.get('class'),
                "confidence": round(p.get('confidence', 0) * 100, 2),
                # إرجاع الإحداثيات اللازمة لرسم الإطار
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
            "message": "Diagnosis completed successfully (via SDK).",
            "predictions": diagnosis_results,
            **base_response
        }, status=status.HTTP_200_OK)