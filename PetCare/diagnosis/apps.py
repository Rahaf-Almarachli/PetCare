from django.apps import AppConfig
import os
import pickle
from django.conf import settings

class DiagnosisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'diagnosis'
    
    # تعريف المتغيرات لتخزين النموذج والمُحوّل (ستكون متاحة عبر DiagnosisConfig.symptoms_model)
    symptoms_model = None
    label_encoder = None

    def ready(self):
        # يتم استدعاء هذه الدالة مرة واحدة فقط عند بدء تشغيل Django
        
        # 1. بناء المسارات الكاملة
        # نستخدم os.path.join لضمان عمل المسارات على Render أو جهازك المحلي
        model_path = os.path.join(settings.BASE_DIR, 'diagnosis', 'ml_models', 'symptoms_model.pkl')
        encoder_path = os.path.join(settings.BASE_DIR, 'diagnosis', 'ml_models', 'label_encoder.pkl')

        # 2. تحميل النموذج والمُحوّل
        try:
            with open(model_path, 'rb') as f:
                DiagnosisConfig.symptoms_model = pickle.load(f)
            
            with open(encoder_path, 'rb') as f:
                DiagnosisConfig.label_encoder = pickle.load(f)

            print("✅ Symptoms Model and Label Encoder loaded successfully.")
            
        except FileNotFoundError:
            # رسالة خطأ واضحة إذا لم يتم العثور على الملفات
            print(f"❌ Error: Model or Encoder file not found. Please ensure they are in: {os.path.join(settings.BASE_DIR, 'diagnosis', 'ml_models')}")
        except Exception as e:
            # رسالة خطأ لأي مشكلة تحميل أخرى (مثل مشكلة توافق المكتبات)
            print(f"❌ Error loading ML model. Check scikit-learn version compatibility: {e}")