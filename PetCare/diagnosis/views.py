import logging
import os
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .ml_model import predict # لاستخدام دالة التشخيص القائمة على الأعراض

# استيراد مكتبة Roboflow
try:
    from roboflow import Roboflow
except ImportError:
    # هذا يسمح للبرنامج بالعمل حتى لو لم يتم تثبيت roboflow، ولكنه يفشل نقطة النهاية الخاصة بالصور
    Roboflow = None 

logger = logging.getLogger(__name__)

# --- 1. التشخيص المعتمد على الأعراض (النموذج المحلي) ---

@api_view(['POST'])
def diagnose_by_symptoms(request):
    """
    نقطة نهاية API للتشخيص المعتمد على الأعراض (JSON POST).
    """
    symptoms = request.data

    if not isinstance(symptoms, dict):
         return Response(
            {"error": "JSON body must be a dictionary of symptoms and their values (0 or 1)."},
            status=status.HTTP_400_BAD_REQUEST
        )

    disease, confidence = predict(symptoms)

    if disease == "خطأ في تحميل النموذج":
         return Response(
            {"error": "Internal server error: The machine learning model failed to load."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({
        "disease": disease,
        "confidence": confidence
    }, status=status.HTTP_200_OK)


# --- 2. التشخيص المعتمد على الصور (Roboflow API) ---

class CatDiagnosisView(APIView):
    """
    نقطة نهاية API للتشخيص المعتمد على صور جلد القطط باستخدام Roboflow.
    تتطلب طلب POST مع 'image_file' في request.FILES.
    """
    def post(self, request, *args, **kwargs):
        if Roboflow is None:
            return Response(
                {"detail": "Roboflow library is not installed on the server."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        # 1. التحقق من وجود الصورة
        image_file: InMemoryUploadedFile = request.FILES.get('image_file')
        if not image_file:
            return Response(
                {"detail": "Image file is missing..."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. إعداد مفاتيح Roboflow وفصل معرّفات المشروع والإصدار (يجب إضافتها في settings.py)
        api_key = getattr(settings, 'ROBOFLOW_API_KEY', None)
        model_endpoint = getattr(settings, 'ROBOFLOW_MODEL_ENDPOINT', None)

        if not api_key or not model_endpoint:
            logger.error("Roboflow settings are missing.")
            return Response(
                {"detail": "Roboflow API Key or Model Endpoint is not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        try:
            # مثال: 'workspace_name/project_name/version_id'
            project_path, version_id = model_endpoint.rsplit('/', 1)
            workspace_name, project_slug = project_path.split('/', 1)
        except ValueError:
             return Response(
                 {"detail": "ROBOFLOW_MODEL_ENDPOINT format is incorrect. Expected: workspace_name/project_name/version_id"},
                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
             )

        temp_file_path = None
        try:
            # 3. حفظ الملف المؤقت للاستخدام من قبل SDK
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(image_file.read())
                temp_file_path = tmp_file.name

            # 4. المصادقة والتحميل باستخدام SDK 
            rf = Roboflow(api_key=api_key)
            workspace = rf.workspace(workspace_name)
            project = workspace.project(project_slug)
            model = project.version(int(version_id)).model

            # 5. إجراء الاستدلال (Inference)
            roboflow_result = model.predict(temp_file_path, confidence=40).json()

        except Exception as e:
            logger.error(f"Roboflow SDK Inference Failed: {e}")
            return Response(
                {"detail": f"Roboflow SDK Inference Failed. Check project ID/Version, Workspace permissions, or API Key: {e}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        finally:
            # 6. حذف الملف المؤقت (مهم جداً)
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        # 7. معالجة النتائج وإرجاعها
        predictions = roboflow_result.get('predictions', [])
        
        diagnosis_results = [
            {
                "disease": p.get('class'),
                # تحويل نسبة الثقة إلى نسبة مئوية (تقريب لأقرب رقمين عشريين)
                "confidence": round(p.get('confidence', 0) * 100, 2), 
                "location": f"X: {p.get('x')}, Y: {p.get('y')}" 
            }
            for p in predictions
        ]

        return Response({
            "message": "Diagnosis completed successfully (via Roboflow SDK).",
            "predictions": diagnosis_results,
            "raw_response_id": roboflow_result.get('image', {}).get('id')
        }, status=status.HTTP_200_OK)