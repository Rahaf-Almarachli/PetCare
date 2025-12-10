import requests as pushy_http_client
from django.conf import settings
from account.models import User
from .models import PushToken
import logging

# إعداد الـ Logger
logger = logging.getLogger(__name__)

def send_pushy_notification(user_id, title, body, data={}):
    """
    يرسل إشعار Pushy إلى جميع رموز الأجهزة المسجلة لمستخدم معين.
    يستخدم مسار /push ويتضمن معالجة تفصيلية لخطأ 400.
    تم رفع مستوى تسجيل الأخطاء (Logging Level) إلى ERROR لضمان ظهور رسائل التشخيص.
    """
    
    # 1. التحقق من مفتاح API
    secret_key = settings.PUSHY_SECRET_KEY
    if not secret_key:
        logger.error("FATAL: PUSHY_SECRET_KEY is not set in settings. Pushy cannot function.")
        return False
        
    # 2. الحصول على رموز الجهاز للمستخدم
    try:
        user = User.objects.get(id=user_id)
        # الحصول على قائمة بالرموز المميزة (Tokens)
        tokens = list(user.push_tokens.values_list('token', flat=True)) 
    except User.DoesNotExist:
        # 🚨 تغيير مستوى السجل إلى WARNING لضمان ظهوره
        logger.warning(f"User with ID {user_id} not found for push notification.")
        return False
    except Exception as e:
        logger.error(f"FATAL: Error retrieving push tokens for user {user_id}: {e}")
        return False

    if not tokens:
        # 🚨 تغيير مستوى السجل إلى ERROR لضمان ظهوره (تشخيص)
        logger.error(f"DIAGNOSTIC: No push tokens found for user {user_id}. Cannot send notification. Check PushToken table.")
        return False

    # 🚨 التعديل الرئيسي: سجل الرموز التي تحاول استخدامها (نستخدم ERROR لضمان الظهور) 
    # نطبع أول 5 رموز للمراجعة
    logger.error(f"DIAGNOSTIC: Pushy attempting to send to tokens (first 5): {tokens[:5]} for user {user_id}. Total tokens: {len(tokens)}")
    # --------------------------------------------------------

    # 3. بناء حمولة الإشعار (Payload)
    payload = {
        "to": tokens,
        "data": {
            "title": title,
            "body": body,
            **data, # دمج البيانات المخصصة
            "content_available": True 
        },
        "notification": {
            "title": title,
            "body": body,
            "badge": 1, 
            "sound": "default"
        },
        "content_available": True
    }

    # 4. إرسال الطلب إلى Pushy API
    pushy_url = "https://api.pushy.me/push"
    
    headers = {
        "Content-Type": "application/json",
    }
    params = {
        "api_key": secret_key
    }

    try:
        response = pushy_http_client.post(
            pushy_url, 
            json=payload, 
            headers=headers, 
            params=params, 
            timeout=10
        )
        
        # رفع خطأ لأكواد الحالة 4xx أو 5xx
        response.raise_for_status() 

        # التأكد من نجاح الرد من Pushy
        response_data = response.json()
        if response_data.get('success', False):
            logger.info(f"SUCCESS: Push notification sent successfully to {len(tokens)} devices for user {user_id}. Pushy ID: {response_data.get('id')}")
            return True
        else:
            # يسجل أخطاء API المرتجعة داخل حمولة JSON (مثل No recipients)
            pushy_error = response_data.get('error', 'Unknown Pushy API Error')
            logger.error(f"PUSHY API FAILED: Pushy API returned failure for user {user_id}. Error: {pushy_error}")
            return False

    except pushy_http_client.exceptions.HTTPError as http_err:
        # 🚨 يلتقط أخطاء HTTP مثل 400 (Bad Request)
        status_code = http_err.response.status_code
        error_details = 'No specific details provided by Pushy.'
        try:
            # محاولة قراءة رسالة الخطأ المحددة من حمولة JSON الخاصة بـ Pushy
            error_details = http_err.response.json().get('error', http_err.response.text or "Malformed response.")
        except:
            # فشل في قراءة JSON، نستخدم النص الخام
            error_details = http_err.response.text or "Malformed response."
            
        # تسجيل رسالة الخطأ التفصيلية
        logger.error(f"PUSH ERROR HTTP (Status {status_code}) for user {user_id}. Details: {error_details}")
        return False

    except pushy_http_client.exceptions.RequestException as e: 
        # 🚨 يلتقط أخطاء الاتصال العامة (DNS, Timeout, Connection Refused)
        logger.error(f"PUSH CONNECTION FAILED (Network/Timeout) for user {user_id}. Error: {e}")
        return False
    except Exception as e:
        # 🚨 أي خطأ غير متوقع
        logger.error(f"UNEXPECTED ERROR during Pushy process for user {user_id}: {e}")
        return False