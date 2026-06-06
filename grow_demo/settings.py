from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure--n#k4+-p3suxa=&=&0l&a703ws*^d*fuioz8965jn052z9zr)l')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = []
if os.environ.get('CSRF_TRUSTED_ORIGINS'):
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get('CSRF_TRUSTED_ORIGINS').split(',') if origin.strip()]
else:
    origins = []
    vercer_url = os.environ.get('VERCEL_URL')
    vercer_domain = os.environ.get('VERCEL_DOMAIN')
    if vercer_url:
        origins.append(f'https://{vercer_url}')
    if vercer_domain:
        origins.append(f'https://{vercer_domain}')
    origins += ['http://localhost:8000', 'http://127.0.0.1:8000', 'https://tradersadda.com', 'https://www.tradersadda.com']
    CSRF_TRUSTED_ORIGINS = origins


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'plans',
    'wallet',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'grow_demo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'grow_demo.wsgi.application'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')
