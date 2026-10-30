
import os
from pathlib import Path

from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Local development credentials do not override explicitly supplied variables.
if os.environ.get('DJANGO_DEBUG', 'true').lower() == 'true':
    load_dotenv(BASE_DIR / '.env.dev', override=False)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
DEBUG = os.environ.get('DJANGO_DEBUG', 'true').lower() == 'true'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY is required when DEBUG is false.')
    SECRET_KEY = 'django-insecure-local-development-only'

# SECURITY WARNING: don't run with debug turned on in production!
ALLOWED_HOSTS = [host.strip() for host in os.environ.get(
    'DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1'
).split(',') if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get(
    'DJANGO_CSRF_TRUSTED_ORIGINS', ''
).split(',') if origin.strip()]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'modulo.acceso',
    'modulo.anymarket',
    'modulo.informat',
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

ROOT_URLCONF = 'inet_ivs.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'inet_ivs.wsgi.application'
ASGI_APPLICATION = 'inet_ivs.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [os.environ.get('REDIS_URL', 'redis://localhost:6379/0')]},
    },
}

CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    'api_rate_limit': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    },
    'informat_tokens': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    },
}
INFORMAT_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = os.environ.get('DJANGO_TIME_ZONE', 'UTC')
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_WORKER_CONCURRENCY = int(os.environ.get('CELERY_WORKER_CONCURRENCY', '2'))
CELERY_BEAT_SCHEDULE = {
    'sincronizar-usuarios-ivs': {
        'task': 'modulo.acceso.tasks.sincronizar_usuarios_ivs',
        'schedule': 3600.0,
    },
}

ANYMARKET_TOKEN = os.environ.get('ANYMARKET_TOKEN', '')
INFORMAT_TOKEN_PRODUCTOS = os.environ.get('INFORMAT_TOKEN_PRODUCTOS', '')
try:
    INFORMAT_TOKEN_TTL = int(os.environ.get('INFORMAT_TOKEN_TTL', '86400'))
except ValueError as exc:
    raise ImproperlyConfigured('INFORMAT_TOKEN_TTL debe ser un entero entre 60 y 86400 segundos.') from exc
if not 60 <= INFORMAT_TOKEN_TTL <= 86400:
    raise ImproperlyConfigured('INFORMAT_TOKEN_TTL debe ser un entero entre 60 y 86400 segundos.')
try:
    INFORMAT_TIMEOUT = int(os.environ.get('INFORMAT_TIMEOUT', '15'))
except ValueError as exc:
    raise ImproperlyConfigured('INFORMAT_TIMEOUT debe ser un entero entre 1 y 120 segundos.') from exc
if not 1 <= INFORMAT_TIMEOUT <= 120:
    raise ImproperlyConfigured('INFORMAT_TIMEOUT debe ser un entero entre 1 y 120 segundos.')
URLTOKEN = os.environ.get('URLTOKEN', '')
EMPRUT = os.environ.get('EMPRUT', '')
CONID = os.environ.get('CONID', '')
APLID = os.environ.get('APLID', '')
WSPRODUCTOSVENTAS = os.environ.get('WSPRODUCTOSVENTAS', '')
WSCOMERCIAL = os.environ.get('WSCOMERCIAL', '')
INET_PEDIDO_DOCUMENTO = os.environ.get('INET_PEDIDO_DOCUMENTO', '771')
INET_PEDIDO_BODEGA = os.environ.get('INET_PEDIDO_BODEGA', '10')
INET_PEDIDO_SUCURSAL = os.environ.get('INET_PEDIDO_SUCURSAL', '1')
INET_PEDIDO_LISTA = os.environ.get('INET_PEDIDO_LISTA', '1')
INET_PEDIDO_CONDICION = os.environ.get('INET_PEDIDO_CONDICION', '0')
INET_PEDIDO_VENDEDOR = os.environ.get('INET_PEDIDO_VENDEDOR', '85644700')
INET_PEDIDO_CLIENTE = os.environ.get('INET_PEDIDO_CLIENTE', '85644700')
URL_WSCOMERCIAL = os.environ.get('URL_WSCOMERCIAL', '')
URL_WSPRODUCTOSVENTAS = os.environ.get('URL_WSPRODUCTOSVENTAS', '')
ANYMARKET_ENVIRONMENT = os.environ.get('ANYMARKET_ENVIRONMENT', 'production')
ANYMARKET_PLATFORM = os.environ.get('ANYMARKET_PLATFORM', 'INET')
ANYMARKET_ENABLED = os.environ.get('ANYMARKET_ENABLED', 'false').lower() == 'true'
ANYMARKET_TIME_ZONE = os.environ.get('ANYMARKET_TIME_ZONE', 'America/Santiago')
if ANYMARKET_ENABLED:
    CELERY_BEAT_SCHEDULE['sincronizar-pedidos-anymarket'] = {
        'task': 'modulo.anymarket.tasks.sincronizar_pedidos',
        'schedule': 60.0,
    }
    CELERY_BEAT_SCHEDULE['reconciliar-pedidos-anymarket'] = {
        'task': 'modulo.anymarket.tasks.reconciliar_pedidos',
        'schedule': crontab(hour=3, minute=0),
    }


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'inet-ivs'),
        'USER': os.environ.get('POSTGRES_USER', ''),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
        'HOST': os.environ.get('POSTGRES_HOST', '192.168.0.8'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'OPTIONS': {'connect_timeout': 5},
    }
}

if os.environ.get('IVS_SAT_USER'):
    DATABASES['ivs_sat'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('IVS_SAT_DB', 'IVS_SAT'),
        'USER': os.environ['IVS_SAT_USER'],
        'PASSWORD': os.environ.get('IVS_SAT_PASSWORD', ''),
        'HOST': os.environ.get('IVS_SAT_HOST', '192.168.0.8'),
        'PORT': os.environ.get('IVS_SAT_PORT', '5432'),
        'OPTIONS': {'connect_timeout': 5},
    }

if os.environ.get('SQLSERVER_DB'):
    sqlserver_extra_params = ''
    if os.environ.get('SQLSERVER_TRUST_SERVER_CERTIFICATE', 'false').lower() == 'true':
        sqlserver_extra_params = 'TrustServerCertificate=yes;'
    DATABASES['sqlserver'] = {
        'ENGINE': 'mssql',
        'NAME': os.environ['SQLSERVER_DB'],
        'USER': os.environ.get('SQLSERVER_USER', ''),
        'PASSWORD': os.environ.get('SQLSERVER_PASSWORD', ''),
        'HOST': os.environ.get('SQLSERVER_HOST', '192.168.0.10'),
        'PORT': os.environ.get('SQLSERVER_PORT', '1433'),
        'OPTIONS': {
            'python_driver': 'mssql_python',
            'connection_timeout': 5,
            'connection_retries': 0,
            'extra_params': sqlserver_extra_params,
        },
    }

DATABASE_ROUTERS = ['inet_ivs.db_router.ExternalDatabaseRouter']

AUTHENTICATION_BACKENDS = ['modulo.acceso.backends.IVSBackend']
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = os.environ.get('DJANGO_TIME_ZONE', 'UTC')

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
