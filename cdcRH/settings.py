"""
Django settings for CDC Django Edition
"""

from pathlib import Path
import os
import secrets as _secrets_mod
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

_secret_key_env = os.environ.get('DJANGO_SECRET_KEY', '')
if _secret_key_env:
    SECRET_KEY = _secret_key_env
elif os.environ.get('DJANGO_DEBUG', 'True') == 'True':
    
    import warnings
    warnings.warn(
        "\n⚠️  DJANGO_SECRET_KEY não definida no .env! Usando chave temporária aleatória.\n"
        "   Adicione ao seu .env: DJANGO_SECRET_KEY=<chave gerada>\n"
        "   Para gerar: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\"",
        RuntimeWarning, stacklevel=2
    )
    SECRET_KEY = _secrets_mod.token_hex(50)
else:
    raise RuntimeError(
        "CRÍTICO: DJANGO_SECRET_KEY não definida! Defina esta variável no .env antes de iniciar em produção."
    )

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

if DEBUG:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

_hosts_env = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,100.64.206.33,.ngrok-free.app,.ngrok-free.dev,.ngrok.io,.ngrok-free.com')
ALLOWED_HOSTS = [h.strip() for h in _hosts_env.split(',') if h.strip()]


CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app',
    'https://*.ngrok-free.dev',
    'https://*.ngrok-free.com',
    'https://*.ngrok.io',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://poeirao.cdc.org.br',
    'https://177.12.121.46',
]

AUTH_USER_MODEL = 'core.OrangeUser'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'cloudinary',               
    'cloudinary_storage',       
    'core',
    'pim',
    'admin_app',
    'leave',
    'attendance',
    'time_tracking',
    'performance',
    'buzz',
    'claim',
    'payroll',
    'anymail',
    'emails',
    'agenda',
    'recruitment',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  
    'rest_framework.authtoken',                  
    'axes',  
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',  
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.DailyTaskMiddleware',
]

ROOT_URLCONF = 'cdcRH.urls'

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
                'core.context_processors.notifications_processor',
                'core.context_processors.module_permissions_processor',
                'attendance.context_processors.punch_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'cdcRH.wsgi.application'

DB_NAME = os.environ.get('DB_NAME')
if DB_NAME:
    DB_ENGINE = os.environ.get('DB_ENGINE', 'django.db.backends.postgresql')
    if 'django_tenants' in DB_ENGINE:
        DB_ENGINE = 'django.db.backends.postgresql'
        
    db_options = {}
    if 'postgresql' in DB_ENGINE:
        db_options = {
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 5,
            'keepalives_count': 3,
            'connect_timeout': 10,
        }
    elif 'mysql' in DB_ENGINE:
        db_options = {
            'charset': 'utf8mb4',
            'connect_timeout': 10,
        }

    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
            'USER': os.environ.get('DB_USER', ''),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', ''),
            'PORT': os.environ.get('DB_PORT', '5432'),
            # Mantém a conexão TCP aberta por 5 minutos (reduz overhead de handshake SSL com Neon)
            'CONN_MAX_AGE': 300,
            # Keepalive TCP: evita que o Neon feche conexões ociosas
            'OPTIONS': db_options,
        }
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

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'  


CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
    'API_KEY':    os.environ.get('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
}


# Motor de Mídia Definitivo do CDC Core (Roteador S3 / Cloudinary)
DEFAULT_FILE_STORAGE = 'core.storage.MasterStorageRouter'



FCM_SERVER_KEY = os.environ.get('FCM_SERVER_KEY', '')

# Credenciais Google Calendar (OAuth)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache em memória local — sem infraestrutura extra (Redis/Memcached)
# Usado para evitar queries repetidas a cada request (ex: DailyTaskMiddleware, permissões de módulo)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'cdc-rh-cache',
    }
}

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'


SESSION_COOKIE_AGE = 28800            
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   
FILE_UPLOAD_MAX_MEMORY_SIZE  = 10 * 1024 * 1024   


EMAIL_BACKEND = 'emails.backends.CustomEmailBackend'

ANYMAIL = {
    "RESEND_API_KEY": os.environ.get("RESEND_API_KEY")
}

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "onboarding@resend.dev")



RESEND_TEST_EMAIL = os.environ.get("RESEND_TEST_EMAIL", "rh@cdc.org.br")

    

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/minute',   
        'user': '100/minute', 
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),   
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,                    
    'BLACKLIST_AFTER_ROTATION': True,                  
    'UPDATE_LAST_LOGIN': True,                        
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'JTI_CLAIM': 'jti',                                 
    'BLACKLIST_ENABLED': True,
}

X_FRAME_OPTIONS = 'SAMEORIGIN'


if not DEBUG:
    SECURE_SSL_REDIRECT = True             
    SESSION_COOKIE_SECURE = True           
    CSRF_COOKIE_SECURE = True              
    SECURE_HSTS_SECONDS = 31536000        
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True  
    SECURE_HSTS_PRELOAD = True             
    SECURE_BROWSER_XSS_FILTER = True      
    SECURE_CONTENT_TYPE_NOSNIFF = True    
    X_FRAME_OPTIONS = 'SAMEORIGIN'              




_cors_env = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if _cors_env:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_env.split(',') if origin.strip()]
else:
    
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:8081',   
        'http://127.0.0.1:3000',
        'http://10.0.2.2:8000',   
    ]


AXES_FAILURE_LIMIT = 10
AXES_COOLOFF_TIME = timedelta(minutes=5)
AXES_LOCKOUT_URL = '/login/'       
AXES_RESET_ON_SUCCESS = True       
AXES_USERNAME_FORM_FIELD = 'username'
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']  
AXES_LOCKOUT_CALLABLE = 'core.axes_handlers.lockout_response'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  
    'django.contrib.auth.backends.ModelBackend',
]


import os
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{asctime}] {levelname} {message}',
            'style': '{',
            'datefmt': '%d/%m/%Y %H:%M:%S',
        },
    },
    'handlers': {
        'file_errors': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 5 * 1024 * 1024,  
            'backupCount': 5,             
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'file_security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'simple',
            'encoding': 'utf-8',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file_errors', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['file_security'],
            'level': 'WARNING',
            'propagate': False,
        },
        'axes': {
            'handlers': ['file_security', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'CDC Core API',
    'DESCRIPTION': 'Documentação das APIs do Sistema Operacional CDC',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}
