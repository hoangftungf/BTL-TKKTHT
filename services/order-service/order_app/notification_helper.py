import httpx
import jwt
import time
import os
from django.conf import settings

def send_notification(user_id, type_choice, title, message, data=None):
    """
    Sends a notification to a specific user via notification-service.
    Uses JWT signed with the shared JWT_SECRET with is_staff=True to bypass authorization.
    """
    url = os.environ.get('NOTIFICATION_SERVICE_URL', 'http://notification-service:8009')
    jwt_secret = getattr(settings, 'JWT_SECRET', 'your-secret-key-goes-here')
    
    payload = {
        'user_id': str(user_id) if user_id else '00000000-0000-0000-0000-000000000000',
        'is_staff': True,
        'role': 'admin',
        'exp': int(time.time()) + 60
    }
    
    token = jwt.encode(payload, jwt_secret, algorithm='HS256')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    body = {
        'user_id': str(user_id) if user_id else None,
        'type': type_choice,
        'channel': 'in_app',
        'title': title,
        'message': message,
        'data': data or {}
    }
    
    try:
        r = httpx.post(f"{url}/send/", json=body, headers=headers, timeout=5.0)
        return r.status_code == 201
    except Exception as e:
        print(f"Error sending notification to user {user_id}: {e}")
        return False

def notify_admins(title, message, data=None):
    """
    Broadcasts a notification to all admin/staff users.
    1. Fetches all users from auth-service.
    2. Identifies admins and staff.
    3. Calls send_notification for each admin.
    """
    auth_url = os.environ.get('AUTH_SERVICE_URL', 'http://auth-service:8001')
    jwt_secret = getattr(settings, 'JWT_SECRET', 'your-secret-key-goes-here')
    
    payload = {
        'user_id': '00000000-0000-0000-0000-000000000000',
        'role': 'admin',
        'is_staff': True,
        'exp': int(time.time()) + 60
    }
    token = jwt.encode(payload, jwt_secret, algorithm='HS256')
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        r = httpx.get(f"{auth_url}/users/", headers=headers, timeout=5.0)
        if r.status_code == 200:
            users = r.json()
            admin_ids = [u['id'] for u in users if u.get('role') == 'admin' or u.get('is_staff') == True]
            for admin_id in admin_ids:
                send_notification(admin_id, 'system', title, message, data)
            return True
    except Exception as e:
        print(f"Error notifying admins: {e}")
    return False
