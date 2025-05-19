# Hospital Admin Authentication Production Settings Example
# Add these settings to your production settings file

# Set to False for production to enable strict validation
DEBUG = False

# Approved healthcare domain patterns for hospital admin emails
APPROVED_HEALTHCARE_DOMAINS = [
    'medicare.com', 
    'hospital.org', 
    'health.gov', 
    'care.org', 
    'medical.net', 
    'clinic.com', 
    'healthcare.org',
    # Add your country/region-specific healthcare domains here
]

# Healthcare-related domain suffixes for pattern matching
HEALTHCARE_DOMAIN_SUFFIXES = [
    'hospital', 'medical', 'health', 'care', 'clinic', 'healthcare',
    'med', 'doctors', 'physicians', 'nursing', 'pharmacy'
    # Add additional healthcare-related terms specific to your region
]

# Rate limiting settings for security
REST_FRAMEWORK = {
    # Existing REST_FRAMEWORK settings...
    
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '60/minute',
        # Hospital admin specific rate limits
        'hospital_admin_login': '5/minute',  # Strict limit for admin login attempts
        'hospital_admin_2fa': '3/minute',   # Very strict for 2FA verification
    }
}

# Enhanced security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Cache settings for OTP and security features
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'TIMEOUT': 300,  # Default cache timeout: 5 minutes
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    },
    'hospital_auth': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379/2',
        'TIMEOUT': 600,  # 2FA codes timeout: 10 minutes
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Production logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 20,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'api.views.auth.hospital_admin_auth': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Email configuration for sending 2FA codes
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.your-secure-provider.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'secure-noreply@healthcare-platform.org'

# 2FA and security settings
HOSPITAL_ADMIN_2FA = {
    'CODE_TIMEOUT_SECONDS': 600,  # 10 minutes
    'MAX_ATTEMPTS': 5,
    'TRUSTED_DEVICE_DAYS': 30,  # Remember device for 30 days
    'TOTP_ISSUER': 'Healthcare Platform',  # For TOTP apps like Google Authenticator
}
