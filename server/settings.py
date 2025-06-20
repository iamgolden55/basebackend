from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY must be set in environment variables - no fallback for security
try:
    SECRET_KEY = os.environ['SECRET_KEY']
except KeyError:
    # Only allow fallback in development
    if os.environ.get('DEBUG', 'False').lower() == 'true':
        SECRET_KEY = "django-insecure-dev-only-q17f1+uwi)4ohs00y5@s_#u*=z(l_b$8w!-iyz*if9!x_3p!cj"
    else:
        raise Exception("SECRET_KEY environment variable must be set for production")

# JWT settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,basebackend-88c8c04dd3ab.herokuapp.com').split(',')


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "api",
    "rest_framework",
    "corsheaders",
    "rest_framework_simplejwt.token_blacklist",
    'rest_framework_simplejwt',
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Move CORS to the top
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "api.middleware.payment_security.PaymentSecurityMiddleware",
]

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Additional Security Headers
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # Allow inline scripts for admin
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")   # Allow inline styles for admin
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'",)
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)

# HTTPS Settings (enable in production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # For reverse proxy

ROOT_URLCONF = "server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'api', 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "server.wsgi.application"

# Email settings - ENABLE REAL EMAIL SENDING
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@phb.com')

APPEND_SLASH = False

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'api': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# Database settings - works both with Docker and without
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "medic_db"),
        "USER": os.environ.get("POSTGRES_USER", "medic_db"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "publichealth"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),  # Uses 'localhost' by default, 'db' in Docker
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = 'api.CustomUser'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'api.auth.EmailBackend',  # Custom email-based authentication
    'django.contrib.auth.backends.ModelBackend',  # Default Django authentication
]

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files (Uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",  # Add Vite frontend port
    "http://127.0.0.1:5173",  # Add Vite frontend port
    "https://localhost:5173",  # HTTPS frontend port
    "https://127.0.0.1:5173",  # HTTPS frontend port
    "http://192.168.11.196:3000",
]

# CORS Configuration - Never allow all origins in production
CORS_ALLOW_ALL_ORIGINS = False  # Hardcoded for security

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-med-access-token',  # Add our custom medical record access token header
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Payment System Toggle
PAYMENTS_ENABLED = os.environ.get('PAYMENTS_ENABLED', 'false').lower() == 'true'

# Payment Provider Settings
PAYMENT_PROVIDERS = {
    'paystack': {
        'secret_key': os.environ.get('PAYSTACK_SECRET_KEY'),
        'public_key': os.environ.get('PAYSTACK_PUBLIC_KEY'), 
        'webhook_secret': os.environ.get('PAYSTACK_WEBHOOK_SECRET'),
        'callback_url': os.environ.get('PAYSTACK_CALLBACK_URL', 'http://localhost:5173/payment-callback'),
        'urls': {
            'initialize': 'https://api.paystack.co/transaction/initialize',
            'verify': 'https://api.paystack.co/transaction/verify',
            'refund': 'https://api.paystack.co/refund'
        }
    }
}

# Payment Security Settings
PAYMENT_SECURITY = {
    'max_attempts': 3,  # Maximum payment attempts
    'lockout_duration': 30,  # Minutes to lock after max attempts
    'amount_limit': 1000000,  # Maximum amount per transaction
    'daily_limit': 5000000,  # Maximum amount per day
    'allowed_countries': ['NG', 'GH', 'ZA'],  # Allowed countries
    'blocked_ips': [],  # IPs to block
    'rate_limit': {
        'window': 3600,  # 1 hour
        'max_requests': 100  # Maximum requests per window
    }
}

# Security Team Email
SECURITY_TEAM_EMAIL = os.environ.get('SECURITY_TEAM_EMAIL', 'security@yourdomain.com')

# Cache settings for rate limiting
# Cache settings - works both with Docker and without
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),  # Uses localhost by default, 'redis' in Docker
        'OPTIONS': {
            'parser_class': 'redis.connection.DefaultParser',
            'pool_class': 'redis.ConnectionPool',
            'retry_on_timeout': True,
            'socket_timeout': 5,
            'socket_connect_timeout': 5,
        }
    }
}

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER')