"""
Heroku-specific settings that override base settings.
This approach allows deployment to Heroku without modifying the main settings.py file.
"""

import os
import sys
import dj_database_url
from .settings import *  # Import all base settings

# Configure production settings
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Configure Allowed Hosts
ALLOWED_HOSTS = [
    'basebackend.herokuapp.com',
    'basebackend-88c8c04dd3ab.herokuapp.com',
    os.environ.get('ALLOWED_HOST', ''),
]

# Configure Heroku database with fallback to original DB
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=True
    )

# Static files configuration for Heroku using Whitenoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Heroku Redis configuration
if 'REDIS_URL' in os.environ:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL'),
            'OPTIONS': {
                'parser_class': 'redis.connection.DefaultParser',
                'pool_class': 'redis.ConnectionPool',
                'retry_on_timeout': True,
                'socket_timeout': 5,
                'socket_connect_timeout': 5,
            }
        }
    }
else:
    # Local memory cache fallback
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# Security settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS configuration - more restricted for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    # Add your frontend URLs here
    "https://your-frontend-app.herokuapp.com",
    os.environ.get('FRONTEND_URL', ''),
]
# Filter out empty strings
CORS_ALLOWED_ORIGINS = [origin for origin in CORS_ALLOWED_ORIGINS if origin]

# Logging configuration for Heroku
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': sys.stdout,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'api': {  # Add your app name here
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Email configuration for Heroku
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

