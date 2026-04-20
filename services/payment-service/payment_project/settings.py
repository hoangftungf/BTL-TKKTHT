import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,payment-service').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'payment_app',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'payment_project.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.debug', 'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'payment_project.wsgi.application'

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3')
DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}

CACHES = {'default': {'BACKEND': 'django_redis.cache.RedisCache', 'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/6'), 'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'}}}

LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOW_ALL_ORIGINS = DEBUG

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['payment_app.authentication.JWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}

JWT_SECRET = os.environ.get('JWT_SECRET', SECRET_KEY)
ORDER_SERVICE_URL = os.environ.get('ORDER_SERVICE_URL', 'http://localhost:8005')
NOTIFICATION_SERVICE_URL = os.environ.get('NOTIFICATION_SERVICE_URL', 'http://localhost:8009')

# MoMo Configuration
MOMO_PARTNER_CODE = os.environ.get('MOMO_PARTNER_CODE', '')
MOMO_ACCESS_KEY = os.environ.get('MOMO_ACCESS_KEY', '')
MOMO_SECRET_KEY = os.environ.get('MOMO_SECRET_KEY', '')
MOMO_ENDPOINT = os.environ.get('MOMO_ENDPOINT', 'https://test-payment.momo.vn/v2/gateway/api')

# VNPay Configuration
VNPAY_TMN_CODE = os.environ.get('VNPAY_TMN_CODE', '')
VNPAY_HASH_SECRET = os.environ.get('VNPAY_HASH_SECRET', '')
VNPAY_URL = os.environ.get('VNPAY_URL', 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html')
