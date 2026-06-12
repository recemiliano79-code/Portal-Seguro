"""
Django settings for proyecto_acoso project.
Portal Seguro / Sentinel v9.0
"""

from pathlib import Path
from dotenv import load_dotenv
import os
import pymysql

pymysql.install_as_MySQLdb()
pymysql.version_info = (2, 2, 1, "final", 0)

# BASE_DIR primero, siempre
BASE_DIR = Path(__file__).resolve().parent.parent

# Carga .env solo en local, en Railway las vars ya están en el entorno
if os.path.exists(BASE_DIR / '.env'):
    load_dotenv(override=False)

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-cambia-esto-en-produccion')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',
    '.railway.app',
    '.up.railway.app',
    os.getenv('RENDER_EXTERNAL_HOSTNAME', ''),
    os.getenv('RAILWAY_PUBLIC_DOMAIN', ''),
]

CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://*.railway.app',
    'https://*.up.railway.app',
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

INSTALLED_APPS = [
    "pages.apps.PagesConfig",
    "accounts",
    'projects.apps.ProjectsConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'proyecto_acoso.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'proyecto_acoso.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME':     os.getenv('MYSQL_NAME', 'defaultdb'),
        'USER':     os.getenv('MYSQL_USER'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD'),
        'HOST':     os.getenv('MYSQL_HOST'),
        'PORT':     os.getenv('MYSQL_PORT', '15549'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'ssl_disabled': False,
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if os.path.exists(BASE_DIR / 'static') else []
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_ROOT = BASE_DIR / 'uploads'
MEDIA_URL = '/media/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400
SESSION_COOKIE_HTTPONLY = True

logs_dir = BASE_DIR / 'logs'
if not logs_dir.exists():
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

BLACKNOX_API_KEY     = os.getenv('BLACKNOX_API_KEY', '')
BLACKNOX_BASE_URL    = os.getenv('BLACKNOX_BASE_URL', 'https://api.groq.com/openai/v1')
BLACKNOX_MODEL       = os.getenv('BLACKNOX_MODEL', 'gpt-4o')
BLACKNOX_MAX_TOKENS  = int(os.getenv('BLACKNOX_MAX_TOKENS', '1500'))
BLACKNOX_TEMPERATURE = float(os.getenv('BLACKNOX_TEMPERATURE', '0.7'))
BLACKNOX_TIMEOUT     = int(os.getenv('BLACKNOX_TIMEOUT', '60'))

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'sentinel-cache',
    }
}

EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = f'Portal Seguro <{os.getenv("EMAIL_HOST_USER", "")}>'

PASSWORD_RESET_TIMEOUT = 86400