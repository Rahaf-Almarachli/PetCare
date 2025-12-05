import os
import pickle
from django.apps import AppConfig
from django.conf import settings

# متغيرات عامة لحفظ النموذج والمُشفِّر بعد التحميل
DOG_SYMPTOMS_MODEL = None
DOG_DISEASE_ENCODER = None

class DiagnosisConfig(AppConfig):
    # الاسم الافتراضي لتطبيقك
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'diagnosis'

    def ready(self):
        """
        تحميل نماذج التعلم الآلي لتكون متاحة للـ Views.
        تمت إضافة منطق مرن للتعامل مع أخطاء تسمية الملفات الشائعة (مثل وجود (1) في الاسم).
        **تم إضافة: encoding='latin1' لحل مشكلة STACK_GLOBAL.**
        """
        global DOG_SYMPTOMS_MODEL
        global DOG_DISEASE_ENCODER

        # المسارات المتوقعة لملفات النموذج والمُشفِّر (الأسماء النظيفة والمفضلة)
        MODEL_PATH = os.path.join(settings.BASE_DIR, 'diagnosis', 'ml_models', 'dog_disease_model.pkl')
        ENCODER_PATH_CLEAN = os.path.join(settings.BASE_DIR, 'diagnosis', 'ml_models', 'disease_label_encoder.pkl')
        
        # مسار بديل للتعامل مع ملف "disease_label_encoder (1).pkl"
        ENCODER_PATH_FALLBACK = os.path.join(settings.BASE_DIR, 'diagnosis', 'ml_models', 'disease_label_encoder (1).pkl')

        # تحديد مسار المُشفِّر الذي سيتم استخدامه فعليًا
        if os.path.exists(ENCODER_PATH_CLEAN):
            ENCODER_PATH = ENCODER_PATH_CLEAN
        elif os.path.exists(ENCODER_PATH_FALLBACK):
            ENCODER_PATH = ENCODER_PATH_FALLBACK
        else:
            ENCODER_PATH = None
        
        # التحقق من وجود ملف النموذج وملف المُشفِّر (أياً كان اسمه)
        if not os.path.exists(MODEL_PATH) or not ENCODER_PATH:
            print("❌❌❌ ERROR: Dog Diagnosis Model or Encoder file not found in ml_models folder. Expected names: 'dog_disease_model.pkl' and 'disease_label_encoder.pkl' (or 'disease_label_encoder (1).pkl'). ❌❌❌")
            DOG_SYMPTOMS_MODEL = None
            DOG_DISEASE_ENCODER = None
            return

        try:
            # 1. تحميل نموذج تشخيص الأعراض
            # **الحل**: استخدام encoding='latin1'
            with open(MODEL_PATH, 'rb') as model_file:
                DOG_SYMPTOMS_MODEL = pickle.load(model_file, encoding='latin1')
            
            # 2. تحميل مُشفِّر التسميات
            # **الحل**: استخدام encoding='latin1'
            with open(ENCODER_PATH, 'rb') as encoder_file:
                DOG_DISEASE_ENCODER = pickle.load(encoder_file, encoding='latin1')

            print(f"✅✅✅ Dog Symptom Diagnosis Models loaded successfully! Model Path: {MODEL_PATH}, Encoder Path: {ENCODER_PATH} ✅✅✅")
            
        except Exception as e:
            # سنحتفظ بتقرير الخطأ لمزيد من التصحيح إذا لم ينجح الحل
            print(f"❌ ERROR DURING MODEL LOADING: {e}")
            DOG_SYMPTOMS_MODEL = None
            DOG_DISEASE_ENCODER = None