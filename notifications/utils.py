import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from .models import DeviceToken
import json
from django.db.models import Q

# 1. تهيئة Firebase مرة واحدة عند تشغيل الوحدة
if settings.FIREBASE_CREDENTIALS:
    try:
        # تحويل بيانات الاعتماد إلى كائن Credential
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
        firebase_admin.initialize_app(cred)
        FIREBASE_INITIALIZED = True
        print("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        print(f"ERROR: Failed to initialize Firebase Admin SDK: {e}")
        FIREBASE_INITIALIZED = False
else:
    FIREBASE_INITIALIZED = False

def send_push_notification(user, title, body, notification_type, object_id):
    """ يرسل إشعار Push Notification لمستخدم معين باستخدام firebase-admin. """
    
    if not FIREBASE_INITIALIZED:
        print("FCM Service not initialized. Aborting.")
        return

    # 1. استخراج الرموز النشطة للجهاز
    tokens = DeviceToken.objects.filter(user=user, is_active=True).values_list('token', flat=True)
    
    if not tokens:
        return

    # 2. إعداد حمولة الإشعار (Payload)
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data={
            "type": notification_type,
            "id": str(object_id),
            # يمكن إضافة بيانات أخرى يحتاجها التطبيق لفتح الشاشة الصحيحة
        },
        tokens=list(tokens),
    )

    # 3. الإرسال الفعلي
    try:
        response = messaging.send_multicast(message)
        # 4. معالجة الاستجابة (لإزالة الرموز غير الصالحة)
        if response.failure_count > 0:
            # ⚠️ يجب عليك هنا تطوير منطق يزيل الرموز التي تم إرجاعها كـ 'NOT_REGISTERED'
            print(f"Successfully sent: {response.success_count}, Failed: {response.failure_count}")
        
    except Exception as e:
        print(f"Error sending push notification via Firebase Admin SDK: {e}")


# ... (بعد كود التهيئة في utils.py)

def send_push_notification(user, title, body, notification_type, object_id):
    """
    يرسل إشعار Push Notification لمستخدم معين باستخدام firebase-admin.
    """
    
    if not FIREBASE_INITIALIZED:
        print("FCM Service not initialized. Cannot send notification.")
        return

    # 1. استخراج جميع الرموز النشطة للمستخدم المستهدف
    tokens = DeviceToken.objects.filter(user=user, is_active=True).values_list('token', flat=True)
    
    if not tokens:
        print(f"No active tokens found for user {user.pk}.")
        return

    # 2. إعداد حمولة الإشعار (Notification + Data)
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data={
            # هذه البيانات تستخدمها تطبيقات Android/iOS لفتح الشاشة الصحيحة
            "type": notification_type, 
            "id": str(object_id),
        },
        tokens=list(tokens),
    )

    # 3. الإرسال الفعلي
    try:
        response = messaging.send_multicast(message)
        # ⚠️ (يجب معالجة الرموز غير الصالحة هنا وإلغاء تنشيطها في قاعدة البيانات)
        if response.failure_count > 0:
             print(f"FCM failure count: {response.failure_count}")

    except Exception as e:
        print(f"Error sending push notification via Firebase Admin SDK: {e}")