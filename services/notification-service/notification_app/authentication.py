import jwt
from django.conf import settings
from rest_framework import authentication, exceptions

class JWTUser:
    def __init__(self, payload):
        self.id = payload.get('user_id')
        self.is_authenticated = True
        self.is_staff = payload.get('is_staff', False)

class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header: return None
        try:
            prefix, token = auth_header.split(' ')
            if prefix.lower() != 'bearer': return None
        except ValueError: return None
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
            return (JWTUser(payload), token)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token đã hết hạn')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Token không hợp lệ')
