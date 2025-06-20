# Production Security Checklist

## 🚨 CRITICAL - Must Fix Before Production

### 1. Environment & Secrets Management
- [ ] **Remove .env file from version control**
  ```bash
  git rm .env
  echo ".env" >> .gitignore
  git commit -m "Remove sensitive environment file"
  ```
- [ ] **Change all exposed credentials**
  - [ ] Generate new SECRET_KEY
  - [ ] Rotate all payment API keys
  - [ ] Update email app passwords
  - [ ] Generate new database passwords
- [ ] **Use production secret management**
  - [ ] AWS Secrets Manager / Azure Key Vault / HashiCorp Vault
  - [ ] Environment-specific secret injection

### 2. Authentication Security
- [ ] **Fix hardcoded SECRET_KEY fallback**
  ```python
  # Change this:
  SECRET_KEY = os.environ.get('SECRET_KEY', "django-insecure-...")
  # To this:
  SECRET_KEY = os.environ['SECRET_KEY']  # Fail fast if missing
  ```
- [ ] **Implement secure token hashing**
  ```python
  import hashlib
  def hash_token(token):
      return hashlib.sha256(token.encode()).hexdigest()
  ```
- [ ] **Add password complexity requirements**
- [ ] **Implement session invalidation on suspicious activity**

### 3. Production Settings Hardening
- [ ] **Disable debug mode permanently**
  ```python
  DEBUG = False  # Hardcode for production
  ```
- [ ] **Configure specific ALLOWED_HOSTS**
  ```python
  ALLOWED_HOSTS = ['yourdomain.com', 'api.yourdomain.com']
  ```
- [ ] **Remove CORS_ALLOW_ALL_ORIGINS option entirely**
- [ ] **Enable all security headers**

## 🔒 HIGH PRIORITY - Security Improvements

### 4. Data Protection Enhancements
- [ ] **Fix encryption key derivation**
  ```python
  from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
  # Use proper KDF instead of simple concatenation
  ```
- [ ] **Implement database-level encryption**
- [ ] **Add field-level encryption for PII**
- [ ] **Secure file upload validation**

### 5. API Security
- [ ] **Remove any raw SQL queries**
- [ ] **Implement comprehensive input validation**
- [ ] **Add API rate limiting**
- [ ] **Implement request/response logging**

### 6. Medical Data Compliance (HIPAA)
- [ ] **Implement comprehensive audit logging**
- [ ] **Add data retention policies**
- [ ] **Create breach detection system**
- [ ] **Implement role-based access controls**

## ⚙️ MEDIUM PRIORITY - Production Readiness

### 7. Monitoring & Logging
- [ ] **Set up centralized logging**
- [ ] **Implement security event monitoring**
- [ ] **Add performance monitoring**
- [ ] **Configure alerting system**

### 8. Infrastructure Security
- [ ] **Database connection encryption**
- [ ] **Regular security scanning**
- [ ] **Backup encryption**
- [ ] **Network security policies**

### 9. Incident Response
- [ ] **Security incident response plan**
- [ ] **Data breach notification procedures**
- [ ] **Recovery procedures**
- [ ] **Staff security training**

## 📋 Security Configuration Templates

### Production Settings Example
```python
# server/settings/production.py
import os
from .base import *

# Security
DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = ['yourdomain.com', 'api.yourdomain.com']

# HTTPS Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Database Security
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['POSTGRES_DB'],
        'USER': os.environ['POSTGRES_USER'],
        'PASSWORD': os.environ['POSTGRES_PASSWORD'],
        'HOST': os.environ['POSTGRES_HOST'],
        'PORT': os.environ['POSTGRES_PORT'],
        'OPTIONS': {
            'sslmode': 'require',  # Require SSL
        },
    }
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/app.log',
            'formatter': 'verbose',
        },
        'security': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/security.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security'],
            'level': 'WARNING',
            'propagate': True,
        },
        'api': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Secure Token Management
```python
# api/utils/security.py
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

class SecureTokenManager:
    @staticmethod
    def generate_token():
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token):
        """Hash token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def derive_key(password, salt):
        """Derive encryption key using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())
```

## 🔍 Security Testing Checklist

### Automated Security Testing
- [ ] **OWASP ZAP security scan**
- [ ] **Bandit Python security scan**
- [ ] **Safety dependency vulnerability scan**
- [ ] **SQL injection testing**

### Manual Security Testing
- [ ] **Authentication bypass testing**
- [ ] **Authorization escalation testing**
- [ ] **Input validation testing**
- [ ] **Session management testing**

### Compliance Testing
- [ ] **HIPAA compliance audit**
- [ ] **Data privacy assessment**
- [ ] **Audit trail verification**
- [ ] **Encryption validation**

## 📊 Security Metrics

### Key Performance Indicators
- Authentication failure rate < 1%
- API response time < 200ms
- Security incident count = 0
- Compliance score > 95%

### Monitoring Alerts
- Failed login attempts > 5/minute
- Unusual API access patterns
- Database connection failures
- SSL certificate expiration warnings

## 🚀 Deployment Security Process

1. **Pre-deployment Security Review**
   - Code security scan
   - Dependency vulnerability check
   - Configuration review
   - Penetration testing

2. **Deployment Security**
   - Secure CI/CD pipeline
   - Infrastructure as Code
   - Automated security testing
   - Rollback procedures

3. **Post-deployment Monitoring**
   - Real-time security monitoring
   - Automated threat detection
   - Incident response procedures
   - Regular security assessments

## 📞 Emergency Contacts

- **Security Team**: security@yourdomain.com
- **DevOps Team**: devops@yourdomain.com
- **CISO**: ciso@yourdomain.com
- **Legal/Compliance**: legal@yourdomain.com

---

**Last Updated**: [Current Date]
**Next Review**: [Date + 30 days]
**Approved By**: [Security Team Lead]