# apps.py - إعدادات تطبيق التشخيص وتحميل النموذج

import os
import pickle
from django.apps import AppConfig
from django.conf import settings
# لم يعد هناك حاجة لاستيراد constants هنا، لكن سنتركها إذا كان الكود القديم يتطلبها

# متغيرات عامة لحفظ النموذج والمُشفِّر بعد التحميل
# نستخدم اسم متغير واضح لنموذج الكلاب
DOG_SYMPTOMS_MODEL = None
DOG_DISEASE_ENCODER = None

class DiagnosisConfig(AppConfig):
    # الاسم الافتراضي لتطبيقك، تأكدي من مطابقته
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'diagnosis'

    def ready(self):
        """
        يتم استدعاء هذه الدالة مرة واحدة عند بدء تشغيل تطبيق Django.
        نقوم فيها بتحميل نماذج التعلم الآلي لتكون متاحة للـ Views.
        """
        global DOG_SYMPTOMS_MODEL
        global DOG_DISEASE_ENCODER

        # تحديد المسارات المتوقعة لملفات النموذج والمُشفِّر
        # dog_disease_model.pkl هو الاسم الجديد الذي قمتِ برفعه
        MODEL_PATH = os.path.join(settings.BASE_DIR, 'diagnosis', 'ml_models', 'dog_disease_model.pkl')
        # disease_label_encoder.pkl هو الاسم المُعاد تسميته
        ENCODER_PATH = os.path.join(settings.BASE_DIR, 'diagnosis', 'ml_models', 'disease_label_encoder.pkl')

        # تأكد من أن ملفات النموذج موجودة قبل محاولة التحميل
        if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
            # نستخدم طباعة باللغة الإنجليزية لتظهر بشكل صحيح في سجلات Render
            print("❌❌❌ ERROR: Dog Diagnosis Model or Encoder file not found in ml_models folder. Check file names. ❌❌❌")
            DOG_SYMPTOMS_MODEL = None
            DOG_DISEASE_ENCODER = None
            return

        try:
            # 1. تحميل نموذج تشخيص الأعراض
            with open(MODEL_PATH, 'rb') as model_file:
                DOG_SYMPTOMS_MODEL = pickle.load(model_file)
            
            # 2. تحميل مُشفِّر التسميات
            with open(ENCODER_PATH, 'rb') as encoder_file:
                DOG_DISEASE_ENCODER = pickle.load(encoder_file)

            print("✅✅✅ Dog Symptom Diagnosis Models loaded successfully! ✅✅✅")
            
        except Exception as e:
            print(f"❌ ERROR DURING MODEL LOADING: {e}")
            DOG_SYMPTOMS_MODEL = None
            DOG_DISEASE_ENCODER = None