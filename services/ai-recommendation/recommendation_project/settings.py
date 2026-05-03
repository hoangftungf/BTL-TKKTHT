import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,ai-recommendation').split(',')

INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'rest_framework', 'corsheaders', 'recommendation_app']
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware', 'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'recommendation_project.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.debug', 'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'recommendation_project.wsgi.application'

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3')
DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}

CACHES = {'default': {'BACKEND': 'django_redis.cache.RedisCache', 'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/10'), 'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'}}}

LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOW_ALL_ORIGINS = DEBUG

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['recommendation_app.authentication.JWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
}

JWT_SECRET = os.environ.get('JWT_SECRET', SECRET_KEY)
PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://localhost:8003')
ORDER_SERVICE_URL = os.environ.get('ORDER_SERVICE_URL', 'http://localhost:8005')

# Model paths
MODEL_DIR = BASE_DIR / 'models'

# Neo4j Knowledge Graph
NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://neo4j:7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'password123')

# Ollama LLM for RAG
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://ollama:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'recommendation_app': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
