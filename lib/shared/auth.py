"""
Shared User Read Model + JWT Authentication Helper
====================================================
Thay thế duplicated authentication.py ở mọi service.

Usage:
    from lib.shared.auth import JWTAuthentication, UserReadModel

    # Trong DRF settings:
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'lib.shared.auth.JWTAuthentication',
        ],
    }

    # Lấy user info mà không cần gọi auth-service:
    user = UserReadModel.get_by_id(user_id)
"""
import jwt
import time
import logging
from typing import Any, Dict, List, Optional
from django.conf import settings
from rest_framework import authentication, exceptions

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared JWT User
# ---------------------------------------------------------------------------

class JWTUser:
    """Minimal User representation decoded from JWT token.

    Dùng chung cho tất cả services thay vì mỗi service tự define.
    """
    def __init__(self, payload: dict):
        self.id = payload.get("user_id")
        self.email = payload.get("email", "")
        self.is_staff = payload.get("is_staff", False)
        self.role = payload.get("role", "customer")
        self.is_authenticated = True

    def __str__(self):
        return str(self.id)


class JWTAuthentication(authentication.BaseAuthentication):
    """Shared JWT Authentication — thay thế mọi file authentication.py riêng lẻ."""

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        try:
            prefix, token = auth_header.split(" ")
            if prefix.lower() != "bearer":
                return None
        except ValueError:
            return None

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=["HS256"],
            )
            return (JWTUser(payload), token)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token đã hết hạn")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Token không hợp lệ")


# ---------------------------------------------------------------------------
# User Read Model — local cache tránh gọi auth-service liên tục
# ---------------------------------------------------------------------------

class UserReadModel:
    """Read-model cho User data, cached locally.

    Tránh gọi HTTP tới auth-service mỗi lần cần thông tin user.
    Cache TTL 5 phút, tự động refresh.
    """

    _cache: Dict[str, Any] = {}
    _admin_cache: List[Dict] = []
    _admin_cache_time: float = 0
    _admin_cache_ttl: int = 300  # 5 phút

    @classmethod
    def get_by_id(cls, user_id: str) -> Optional[Dict]:
        """Lấy user info từ cache hoặc auth-service API.

        Returns dict với {id, email, role, is_staff, full_name} hoặc None.
        """
        # Check cache
        if user_id in cls._cache:
            return cls._cache[user_id]

        # Fetch from auth-service
        try:
            import httpx
            import os
            auth_url = os.environ.get("AUTH_SERVICE_URL", "http://auth-service:8001")
            jwt_secret = getattr(settings, "JWT_SECRET", "your-secret-key")
            token = jwt.encode(
                {
                    "user_id": "00000000-0000-0000-0000-000000000000",
                    "role": "admin",
                    "is_staff": True,
                    "exp": int(time.time()) + 30,
                },
                jwt_secret,
                algorithm="HS256",
            )
            response = httpx.get(
                f"{auth_url}/users/{user_id}/",
                headers={"Authorization": f"Bearer {token}"},
                timeout=3.0,
            )
            if response.status_code == 200:
                data = response.json()
                cls._cache[user_id] = data
                return data
        except Exception as e:
            logger.warning(f"UserReadModel.get_by_id({user_id}) failed: {e}")

        return None

    @classmethod
    def get_admins(cls) -> List[Dict]:
        """Lấy danh sách admin/staff — cached 5 phút.

        Returns list of dicts [{id, email, role, is_staff, full_name}].
        """
        from django.utils import timezone
        now = time.time()
        if cls._admin_cache and (now - cls._admin_cache_time) < cls._admin_cache_ttl:
            return cls._admin_cache

        try:
            import httpx
            import os
            auth_url = os.environ.get("AUTH_SERVICE_URL", "http://auth-service:8001")
            jwt_secret = getattr(settings, "JWT_SECRET", "your-secret-key")
            token = jwt.encode(
                {
                    "user_id": "00000000-0000-0000-0000-000000000000",
                    "role": "admin",
                    "is_staff": True,
                    "exp": int(time.time()) + 30,
                },
                jwt_secret,
                algorithm="HS256",
            )
            response = httpx.get(
                f"{auth_url}/users/",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0,
            )
            if response.status_code == 200:
                users = response.json()
                admins = [u for u in users if u.get("role") == "admin" or u.get("is_staff") is True]
                cls._admin_cache = admins
                cls._admin_cache_time = now
                return admins
        except Exception as e:
            logger.warning(f"UserReadModel.get_admins() failed: {e}")

        return cls._admin_cache  # return stale cache nếu có

    @classmethod
    def invalidate_cache(cls, user_id: Optional[str] = None):
        """Clear cache cho 1 user hoặc toàn bộ."""
        if user_id:
            cls._cache.pop(user_id, None)
        else:
            cls._cache.clear()
            cls._admin_cache = []
            cls._admin_cache_time = 0
