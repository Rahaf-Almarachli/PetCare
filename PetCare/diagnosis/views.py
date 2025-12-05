from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging
import os
from roboflow import Roboflow
import tempfile
from django.core.files.uploadedfile import InMemoryUploadedFile
import numpy as np
import json
import pandas as pd # يتم استخدامه لتجهيز البيانات لتغذية النموذج

# ===================================================================================
# التعديل الحاسم: استيراد المتغيرات العامة الجديدة لنموذج الكلاب من apps.py
# وكذلك استيراد قائمة الأعراض من constants.py لتجنب التكرار
# ===================================================================================
from .apps import DOG_SYMPTOMS_MODEL, DOG_DISEASE_ENCODER 
from .constants import SYMPTOMS_LIST, NUM_FEATURES
# ===================================================================================

logger = logging.getLogger(__name__)

# ملاحظة: تم حذف قائمة الأعراض SYMPTOMS_LIST و NUM_FEATURES من هنا 
# وأصبحت تُستورد من ملف constants.py

# ====================================================================
# A. نقطة نهاية تشخيص الصورة (Image Diagnosis Endpoint) - لم تتغير
# ====================================================================

class CatDiagnosisView(APIView):
    """
    Handles image upload for cat diagnosis using Roboflow SDK.
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
        model_endpoint = settings.ROBOFLOW_MODEL_ENDPOINT
        
        try:
            # مثال: workspace_name/project_name/version_id
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
            # نستخدم .jpg كلاحقة افتراضية
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                # التأكد من إعادة تعيين مؤشر الملف إلى البداية قبل القراءة
                image_file.seek(0)
                tmp_file.write(image_file.read())
                temp_file_path = tmp_file.name

            # 4. المصادقة والتحميل باستخدام SDK
            rf = Roboflow(api_key=api_key)
            workspace = rf.workspace()
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
# B. نقطة نهاية تشخيص الأعراض (Symptom Diagnosis Endpoint)
# ====================================================================

class SymptomDiagnosisView(APIView):
    """
    نقطة نهاية لتشخيص المرض بناءً على الأعراض المقدمة في شكل قاموس (Key-Value).
    تقوم بتحويل الأعراض المرسلة إلى متجه (Vector) بحجم 75 لتغذية نموذج الكلاب الجديد.
    """
    def post(self, request, *args, **kwargs):
        # 1. التحقق من تحميل النموذج (باستخدام الأسماء الجديدة DOG_...)
        if DOG_SYMPTOMS_MODEL is None or DOG_DISEASE_ENCODER is None:
            return Response(
                {"detail": "ML Model is not ready. Please ensure dog_disease_model.pkl and disease_label_encoder.pkl are loaded."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # 2. الحصول على بيانات الأعراض
        symptoms_data = request.data
        
        if not isinstance(symptoms_data, dict):
            return Response(
                {"detail": "Invalid input format. Expected a JSON object mapping symptom names to 1 or 0."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 3. بناء متجه الأعراض (Mapping)
            input_vector = np.zeros(NUM_FEATURES, dtype=int)
            
            valid_symptom_found = False
            
            # المرور على البيانات المرسلة من Flutter وتعيين القيمة 1 في الفهرس الصحيح
            for symptom_name, value in symptoms_data.items():
                
                # تطابق اسم العرض مع القائمة الرسمية (SYMPTOMS_LIST)
                try:
                    # نجد فهرس العرض في قائمتنا الرئيسية
                    index = SYMPTOMS_LIST.index(symptom_name)
                    
                    # نضع 1 في ذلك الفهرس في المتجه إذا كانت القيمة المرسلة هي 1
                    if value == 1:
                        input_vector[index] = 1
                        valid_symptom_found = True
                    
                except ValueError:
                    # إذا أرسل Flutter اسماً غير موجود في قائمة الأعراض الـ 75 (نتجاهله)
                    logger.warning(f"Ignoring unknown symptom sent from frontend: {symptom_name}")
                    continue
            
            # التأكد من أن المتجه ليس فارغاً تماماً
            if not valid_symptom_found:
                 return Response(
                     {"detail": "No valid symptoms were marked as present (1). Please select at least one symptom."},
                     status=status.HTTP_400_BAD_REQUEST
                 )

            # 4. تجهيز البيانات وإجراء التوقع
            # إنشاء DataFrame بالبيانات لضمان التوافق مع النموذج
            input_data = {SYMPTOMS_LIST[i]: input_vector[i] for i in range(NUM_FEATURES)}
            symptoms_df = pd.DataFrame([input_data]) 

            # إجراء التوقع (باستخدام المتغير العام الجديد DOG_SYMPTOMS_MODEL)
            prediction_index = DOG_SYMPTOMS_MODEL.predict(symptoms_df)[0]
            
            # 5. تحويل الفهرس الرقمي إلى اسم المرض المقابل (باستخدام DOG_DISEASE_ENCODER)
            predicted_disease = DOG_DISEASE_ENCODER.inverse_transform([prediction_index])[0]
            
            # 6. إرجاع النتيجة
            return Response({
                "message": "Diagnosis completed successfully based on symptoms (Dog Model).",
                "predicted_disease": predicted_disease.strip(),
                "model_used": "dog_disease_model.pkl"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Symptom Prediction Error: {e}")
            return Response(
                {"detail": f"An unexpected error occurred during symptom prediction: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )