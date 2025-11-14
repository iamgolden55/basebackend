"""
Messaging System Configuration for Auto-Scaling Storage

Add these settings to your Django settings.py file to configure
the auto-scaling message storage system.
"""

# ===============================================
# Auto-Scaling Storage Configuration
# ===============================================

# Storage strategy: 'local', 'hybrid', 'firebase', or 'auto' (recommended)
MESSAGE_STORAGE_STRATEGY = 'auto'  # Auto-scaling based on thresholds

# Auto-scaling thresholds
AUTO_SCALE_HYBRID_THRESHOLD = 5_000_000      # Switch to Hybrid at 5M messages
AUTO_SCALE_FIREBASE_THRESHOLD = 50_000_000   # Switch to Firebase at 50M messages

# Performance thresholds that trigger scaling
AUTO_SCALE_MAX_RESPONSE_TIME = 500           # Max DB response time (ms)
AUTO_SCALE_MAX_DB_SIZE = 100                 # Max DB size (GB)
AUTO_SCALE_MAX_CONCURRENT_USERS = 1000       # Max concurrent users
AUTO_SCALE_MAX_MESSAGE_RATE = 10000          # Max messages per hour

# Hybrid strategy settings
MESSAGE_LOCAL_RETENTION_DAYS = 30            # Keep recent messages locally

# Message encryption (REQUIRED for HIPAA compliance)
MESSAGE_ENCRYPTION_KEY = 'your-256-bit-key-here'  # Generate with Fernet.generate_key()

# ===============================================
# Firebase Configuration (for cloud scaling)
# ===============================================

# Firebase settings (required when scaling to Firebase)
FIREBASE_PROJECT_ID = 'your-hipaa-compliant-project'
FIREBASE_SERVICE_ACCOUNT_KEY = '/path/to/service-account-key.json'

# Alternative: Use environment variables for Firebase
import os
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
FIREBASE_SERVICE_ACCOUNT_KEY = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')

# ===============================================
# HIPAA Compliance Settings
# ===============================================

# Audit logging
MESSAGE_AUDIT_ENABLED = True
MESSAGE_AUDIT_RETENTION_YEARS = 7           # HIPAA requirement
MESSAGE_AUDIT_HIGH_RISK_ALERT = True        # Real-time alerts for high-risk actions

# Data retention
MESSAGE_DEFAULT_RETENTION_DAYS = 2555       # 7 years (HIPAA standard)
MESSAGE_AUTO_DELETE_ENABLED = False         # Set to True for automatic deletion
MESSAGE_BACKUP_ENABLED = True               # Backup before deletion

# Security
MESSAGE_VIRUS_SCAN_ENABLED = True           # Scan all file attachments
MESSAGE_WATERMARK_ENABLED = True            # Watermark medical images
MESSAGE_ACCESS_LOGGING = True               # Log all file access

# ===============================================
# Performance and Caching
# ===============================================

# Redis settings for real-time features
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery settings for background tasks
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# ===============================================
# Example Production Configuration
# ===============================================

"""
# production_settings.py

# Auto-scaling for large healthcare networks
MESSAGE_STORAGE_STRATEGY = 'auto'
AUTO_SCALE_HYBRID_THRESHOLD = 10_000_000     # 10M for large hospitals
AUTO_SCALE_FIREBASE_THRESHOLD = 100_000_000  # 100M for hospital networks

# High-performance thresholds
AUTO_SCALE_MAX_RESPONSE_TIME = 200           # 200ms for better UX
AUTO_SCALE_MAX_CONCURRENT_USERS = 5000       # Support 5k concurrent users

# HIPAA-compliant Firebase setup
FIREBASE_PROJECT_ID = 'your-baa-project'
FIREBASE_SERVICE_ACCOUNT_KEY = {
    "type": "service_account",
    "project_id": "your-baa-project",
    "private_key_id": "...",
    "private_key": "...",
    # ... (rest of service account key)
}

# Enhanced security
MESSAGE_ENCRYPTION_KEY = os.getenv('MESSAGE_ENCRYPTION_KEY')  # From secure vault
MESSAGE_VIRUS_SCAN_ENABLED = True
MESSAGE_ACCESS_LOGGING = True
MESSAGE_AUDIT_HIGH_RISK_ALERT = True

# Performance optimization
MESSAGE_LOCAL_RETENTION_DAYS = 7            # Only 7 days local for fast access
MESSAGE_CACHE_TIMEOUT = 300                 # 5 minute cache for frequent queries
"""

# ===============================================
# Monitoring and Alerts
# ===============================================

# Email settings for security alerts
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-server.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'alerts@yourhospital.com'
EMAIL_HOST_PASSWORD = 'your-smtp-password'

# Administrators who receive security alerts
ADMINS = [
    ('Healthcare IT Security', 'security@yourhospital.com'),
    ('Platform Administrator', 'admin@yourhospital.com'),
]

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/messaging.log',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/messaging_security.log',
        },
    },
    'loggers': {
        'messaging.autoscaling': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'messaging.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'messaging.audit': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# ===============================================
# Development vs Production
# ===============================================

# Development settings (local only)
if DEBUG:
    MESSAGE_STORAGE_STRATEGY = 'local'
    AUTO_SCALE_HYBRID_THRESHOLD = 100_000      # Lower thresholds for testing
    AUTO_SCALE_FIREBASE_THRESHOLD = 500_000
    MESSAGE_ENCRYPTION_KEY = 'dev-key-change-in-production'
    
# Production settings
else:
    MESSAGE_STORAGE_STRATEGY = 'auto'
    AUTO_SCALE_HYBRID_THRESHOLD = 5_000_000
    AUTO_SCALE_FIREBASE_THRESHOLD = 50_000_000
    MESSAGE_ENCRYPTION_KEY = os.getenv('MESSAGE_ENCRYPTION_KEY')
    
    # Enable all security features in production
    MESSAGE_VIRUS_SCAN_ENABLED = True
    MESSAGE_AUDIT_HIGH_RISK_ALERT = True
    MESSAGE_ACCESS_LOGGING = True