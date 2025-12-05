from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging
import os
from roboflow import Roboflow # المكتبة الرسمية
import tempfile
from django.core.files.uploadedfile import InMemoryUploadedFile
import numpy as np # [جديد] لإجراء عمليات التوقع على المصفوفات
from .apps import DiagnosisConfig # [جديد] لاستيراد النموذج المحمّل من الذاكرة

logger = logging.getLogger(__name__)

# ====================================================================
# A. نقطة نهاية تشخيص الصورة (الكود الأصلي الذي قدمته)
# ====================================================================

class CatDiagnosisView(APIView):
    """
    العـودة إلى الاكتشاف التلقائي لـ Workspace (rf.workspace()) ومحاولة إيجاد المشروع.
    """

    def post(self, request, *args, **kwargs):
        # 1. التحقق من وجود الصورة
        image_file: InMemoryUploadedFile = request.FILES.get('image_file')
        if not image_file:
            return Response(
                {"detail": "Image file is missing..."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. إعداد مفاتيح Roboflow وفصل معرّفات المشروع والإصدار
        api_key = settings.ROBOFLOW_API_KEY
        model_endpoint = settings.ROBOFLOW_MODEL_ENDPOINT # القيمة: maria-angelica-kngdu/skin-disease-of-cat/1
        
        try:
            # project_path سيكون 'maria-angelica-kngdu/skin-disease-of-cat'
            project_path, version_id = model_endpoint.rsplit('/', 1)
            # project_slug سيكون 'skin-disease-of-cat'
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

            # 4. المصادقة والتحميل باستخدام SDK (التصحيح الحاسم)
            rf = Roboflow(api_key=api_key)
            
            # العودة إلى اكتشاف الـ Workspace الافتراضية المرتبطة بالمفتاح
            workspace = rf.workspace()
            
            # محاولة البحث عن المشروع في الـ Workspace الافتراضية
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


# ====================================================================
# B. نقطة نهاية تشخيص الأعراض (المنطق الجديد)
# ====================================================================

class SymptomDiagnosisView(APIView):
    """
    نقطة نهاية لتشخيص المرض بناءً على قائمة الأعراض المقدمة، باستخدام النموذج المُحمّل.
    تتطلب تشغيل خطوات apps.py لتحميل النموذج.
    """
    def post(self, request, *args, **kwargs):
        # 1. التحقق من تحميل النموذج
        if DiagnosisConfig.symptoms_model is None or DiagnosisConfig.label_encoder is None:
            return Response(
                {"detail": "ML Model is not ready. Please ensure symptoms_model.pkl and label_encoder.pkl are loaded."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # 2. الحصول على بيانات الأعراض
        # نفترض أن الأعراض تصل كقائمة من 1 و 0 (Vector) 
        symptoms_vector = request.data.get('symptoms_vector')
        
        if not symptoms_vector or not isinstance(symptoms_vector, list):
            return Response(
                {"detail": "Invalid or missing 'symptoms_vector'. Expected a list of 1s and 0s."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 3. تجهيز البيانات وإجراء التوقع
            # تحويل القائمة إلى مصفوفة numpy، وشكلها ليناسب التوقع
            symptoms_array = np.array([symptoms_vector]) 

            # إجراء التوقع
            prediction_index = DiagnosisConfig.symptoms_model.predict(symptoms_array)[0]
            
            # 4. تحويل الفهرس الرقمي إلى اسم المرض المقابل
            predicted_disease = DiagnosisConfig.label_encoder.inverse_transform([prediction_index])[0]

            return Response({
                "message": "Diagnosis completed successfully based on symptoms.",
                "predicted_disease": predicted_disease,
                "model_used": "symptoms_model_v1"
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            # غالباً خطأ في حجم المدخلات (عدد الأعراض غير متطابق)
            return Response(
                {"detail": f"Input size error. Check that 'symptoms_vector' length matches the model input size: {e}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Symptom Prediction Error: {e}")
            return Response(
                {"detail": f"An unexpected error occurred during symptom prediction: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )