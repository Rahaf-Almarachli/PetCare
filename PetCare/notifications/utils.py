import requests as http_client # 🌟 تم التعديل هنا: استخدام اسم مستعار لتجنب التضارب
from django.conf import settings
from account.models import User
from .models import PushToken # نموذج الـ Token
import logging

logger = logging.getLogger(__name__)

def send_pushy_notification(user_id, title, body, data={}):
    """
    يرسل إشعار Pushy إلى جميع رموز الأجهزة المسجلة لمستخدم معين.
    """
    
    # 1. التحقق من مفتاح API
    secret_key = settings.PUSHY_SECRET_KEY
    if not secret_key:
        logger.error("PUSHY_SECRET_KEY is not set in settings.")
        return False
        
    # 2. الحصول على رموز الجهاز للمستخدم
    try:
        user = User.objects.get(id=user_id)
        tokens = list(user.push_tokens.values_list('token', flat=True))
    except User.DoesNotExist:
        logger.warning(f"User with ID {user_id} not found for push notification.")
        return False
    except Exception as e:
        logger.error(f"Error retrieving push tokens for user {user_id}: {e}")
        return False

    if not tokens:
        logger.info(f"No push tokens found for user {user_id}.")
        return False

    # 3. بناء حمولة الإشعار (Payload)
    # يمكن إضافة المزيد من الخيارات هنا حسب متطلبات Flutter
    payload = {
        "to": tokens,
        "data": {
            "title": title,
            "body": body,
            **data, # دمج البيانات المخصصة (مثل action, request_id)
            "content_available": True # للسماح بمعالجة الإشعار في الخلفية
        },
        "notification": {
            "title": title,
            "body": body,
            "badge": 1, # تحديث رقم الشارة (اختياري)
            "sound": "default"
        },
        "content_available": True
    }

    # 4. إرسال الطلب إلى Pushy API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {secret_key}"
    }

    try:
        # 🌟 استخدام http_client بدلاً من requests 🌟
        response = http_client.post("https://api.pushy.me/send", json=payload, headers=headers, timeout=10)
        response.raise_for_status() # رفع خطأ لأكواد الحالة 4xx أو 5xx
        
        # التأكد من نجاح الرد من Pushy
        response_data = response.json()
        if response_data.get('success', False):
            logger.info(f"Push notification sent successfully to {len(tokens)} devices for user {user_id}.")
            return True
        else:
            logger.error(f"Pushy API error for user {user_id}: {response_data.get('error')}")
            return False

    # 🌟 استخدام http_client.exceptions للتعامل مع أخطاء الاتصال 🌟
    except http_client.exceptions.RequestException as e:
        logger.error(f"Pushy request failed (Connection Error) for user {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during Pushy process for user {user_id}: {e}")
        return False