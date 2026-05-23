import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Use environment variable for secret key in production
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-camcap-x9k2m$3n!w7@fj&q8r5t1v0z6y4u')

# Detect if running on Render
IS_RENDER = os.environ.get('RENDER', '') == 'true'

DEBUG = not IS_RENDER

ALLOWED_HOSTS = ['*']
if IS_RENDER:
    RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_EXTERNAL_HOSTNAME:
        ALLOWED_HOSTS = [RENDER_EXTERNAL_HOSTNAME, '.onrender.com']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'converter',
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

ROOT_URLCONF = 'camcap.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'camcap.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = []
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise for production static file serving
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Maximum upload/download size (2GB for large video files)
DATA_UPLOAD_MAX_MEMORY_SIZE = 2147483648
FILE_UPLOAD_MAX_MEMORY_SIZE = 2147483648

# CSRF trusted origins for Render
if IS_RENDER:
    CSRF_TRUSTED_ORIGINS = [f'https://{RENDER_EXTERNAL_HOSTNAME}'] if os.environ.get('RENDER_EXTERNAL_HOSTNAME') else ['https://*.onrender.com']
