"""
Heroku-specific settings that override base settings.
This approach allows deployment to Heroku without modifying the main settings.py file.
"""

import os
import dj_database_url
from .settings import *  # Import all base settings

# Configure production settings
DEBUG = False

# Configure Heroku database
DATABASES['default'] = dj_database_url.config(conn_max_age=600, ssl_require=True)

# Static files configuration for Heroku using Whitenoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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
    "https://your-frontend-app.herokuapp.com",  # Update with your frontend URL
]

