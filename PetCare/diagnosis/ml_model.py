import joblib
import pandas as pd
import numpy as np
import os
import sys

# --- تحديد المسارات وتحميل النموذج ---

# المسارات النسبية: يفترض أن مجلد 'model' يقع في جذر المشروع، بجوار مجلد 'diagnosis'
try:
    # الحصول على جذر المشروع (PetCare/)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODEL_DIR = os.path.join(BASE_DIR, 'model')
    
    # تحديد المسارات الكاملة للملفات
    SVM_MODEL_PATH = os.path.join(MODEL_DIR, "svm_model.pkl")
    FEATURES_PATH = os.path.join(MODEL_DIR, "features.pkl")
    ENCODER_PATH = os.path.join(MODEL_DIR, "disease_label_encoder.pkl")
    
    # تحميل المكونات
    # ملاحظة: تم افتراض أن اسم ملف النموذج هو "svm_model.pkl" كما في مناقشتنا السابقة.
    model = joblib.load(SVM_MODEL_PATH) 
    features = joblib.load(FEATURES_PATH)
    encoder = joblib.load(ENCODER_PATH)
    MODEL_LOADED = True
    print("✅ ML model components loaded successfully.")

except Exception as e:
    # في حال فشل التحميل، يتم تعيين المتغيرات إلى None وإيقاف التحميل
    print(f"ERROR: Failed to load ML model files: {e}. Check 'model/' directory path and contents.")
    model, features, encoder = None, None, None
    MODEL_LOADED = False

# --- دالة التنبؤ ---

def predict(symptoms: dict):
    """
    تجري تنبؤاً بالمرض بناءً على الأعراض المدخلة باستخدام النموذج المحلي.
    
    المدخلات:
        symptoms (dict): قاموس يحتوي على الأعراض الملاحظة (مثلاً: {"Fever": 1}).
                         
    المخرجات:
        tuple: (اسم المرض المتوقع - str, نسبة الثقة في التوقع - float)
    """
    if not MODEL_LOADED:
        return "خطأ في تحميل النموذج", 0.0

    # 1. إنشاء DataFrame باستخدام القائمة الكاملة للميزات
    # يتم ملء الأعراض غير المذكورة بـ 0 تلقائياً
    X = pd.DataFrame([symptoms], columns=features).fillna(0)

    # 2. التأكد من أن القيم محصورة بين 0 و 1 (لبيانات الإدخال الثنائية)
    X = X.clip(0, 1)

    # 3. التنبؤ بالاحتمالات
    probs = model.predict_proba(X)[0]

    # 4. الحصول على فهرس أعلى احتمال
    idx = np.argmax(probs)

    # 5. تحويل الفهرس إلى اسم المرض ونسبة الثقة
    disease = encoder.inverse_transform([idx])[0]
    confidence = probs[idx]

    return disease, float(confidence)