import requests as pushy_http_client
from django.conf import settings
from account.models import User
from .models import PushToken
import logging

logger = logging.getLogger(__name__)

def send_pushy_notification(user_id, title, body, data={}):
    """
    يرسل إشعار Pushy إلى جميع رموز الأجهزة المسجلة لمستخدم معين.
    """
    
    # 1. التحقق من مفتاح API
    # ملاحظة: يجب أن يُرسل مفتاح API السري كـ 'api_key' في معلمة Query String
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
    payload = {
        "to": tokens,
        "data": {
            "title": title,
            "body": body,
            **data, 
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
    # التعديل الرئيسي: تغيير /send إلى /push
    # وإزالة Authorization Header لأن مفتاح Pushy السري يُرسل كمعامل (query parameter)
    
    # المسار الصحيح لنقطة النهاية (Endpoint)
    pushy_url = "https://api.pushy.me/push"
    
    headers = {
        "Content-Type": "application/json",
        # تمت إزالة Authorization Header واستبداله بـ params
    }

    params = {
        "api_key": secret_key
    }

    try:
        # إرسال الطلب مع تمرير api_key كمعامل URL (params)
        response = pushy_http_client.post(
            pushy_url, 
            json=payload, 
            headers=headers, 
            params=params, 
            timeout=10
        )
        
        response.raise_for_status() # رفع خطأ لأكواد الحالة 4xx أو 5xx

        # التأكد من نجاح الرد من Pushy
        response_data = response.json()
        if response_data.get('success', False):
            logger.info(f"Push notification sent successfully to {len(tokens)} devices for user {user_id}.")
            return True
        else:
            # يسجل أخطاء API مثل 'Invalid Token' أو 'No Recipients'
            logger.error(f"Pushy API returned error for user {user_id}: {response_data.get('error')}")
            return False

    except pushy_http_client.exceptions.RequestException as e: 
        # يسجل أخطاء الاتصال مثل 404 أو Timeouts
        logger.error(f"Pushy request failed (Connection Error) for user {user_id}. URL: {pushy_url} Error: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during Pushy process for user {user_id}: {e}")
        return False