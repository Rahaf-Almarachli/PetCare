import requests
import json
from django.conf import settings
from .models import PushToken
from typing import List, Dict, Union

def send_pushy_notification(user_id: int, title: str, body: str, data_payload: Dict[str, Union[str, int]] = None) -> Union[Dict, None]:
    """ترسل إشعاراً فورياً إلى جميع أجهزة المستخدم عبر Pushy.me."""
    
    if data_payload is None:
        data_payload = {}
        
    secret_key = getattr(settings, 'PUSHY_SECRET_KEY', None)
    if not secret_key:
        print("PUSH NOTIFICATION ERROR: PUSHY_SECRET_KEY is not set.")
        return None

    try:
        tokens: List[str] = list(
            PushToken.objects.filter(user_id=user_id).values_list('token', flat=True).distinct()
        )
    except Exception as e:
        print(f"PUSH NOTIFICATION ERROR: Failed to retrieve tokens for user {user_id}: {e}")
        return None
        
    if not tokens:
        return None 

    payload = {
        "to": tokens, 
        "data": data_payload, 
        "notification": {
            "title": title,
            "body": body,
            "sound": "default",
        },
        "priority": "high", 
    }
    
    try:
        response = requests.post(
            'https://api.pushy.me/send',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {secret_key}' 
            },
            data=json.dumps(payload)
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"PUSH NOTIFICATION FAILURE: Error sending notification to Pushy: {e}")
        return None