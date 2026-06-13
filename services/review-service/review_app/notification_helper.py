"""
Notification Helper — sử dụng UserReadModel thay vì gọi auth-service trực tiếp.

Consolidated: dùng chung UserReadModel từ lib/shared/auth.py.
"""
import httpx
import jwt
import time
import os
from django.conf import settings
from lib.shared.auth import UserReadModel


def send_notification(user_id, type_choice, title, message, data=None):
    """
    Sends a notification to a specific user via notification-service.
    Uses JWT signed with the shared JWT_SECRET.
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
    Uses UserReadModel (cached) thay vì gọi auth-service HTTP mỗi lần.
    """
    try:
        admins = UserReadModel.get_admins()
        for admin in admins:
            send_notification(
                admin['id'], 'system', title, message, data
            )
        return True
    except Exception as e:
        print(f"Error notifying admins: {e}")
    return False
