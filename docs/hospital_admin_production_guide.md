# Hospital Admin Secure Login System: Production Migration Guide

## Overview

This document outlines the necessary steps to safely transition the hospital administrator secure login system from development to production environment. The system has been designed with built-in production-ready features that activate when `DEBUG=False` in your Django settings.

## Table of Contents

1. [Email Domain Management](#1-email-domain-management)
2. [Security Configuration](#2-security-configuration)
3. [Environment Setup](#3-environment-setup)
4. [Data Migration](#4-data-migration)
5. [Administrator Communication](#5-administrator-communication)
6. [Verification Process](#6-verification-process)
7. [Monitoring & Support](#7-monitoring--support)
8. [Testing Checklist](#8-testing-checklist)
9. [Rollback Plan](#9-rollback-plan)

## 1. Email Domain Management

In production, the system enforces strict healthcare domain validation.

### Required Actions:

- [ ] **Update Hospital Admin Emails**: Replace development emails with official healthcare domain emails
  ```sql
  UPDATE api_hospitaladmin 
  SET email = 'administrator@hospital-domain.org' 
  WHERE id = <admin_id>;
  ```

- [ ] **Update Associated User Emails**: Ensure the linked CustomUser records have matching emails
  ```sql
  UPDATE api_customuser 
  SET email = 'administrator@hospital-domain.org' 
  WHERE id IN (SELECT user_id FROM api_hospitaladmin WHERE id = <admin_id>);
  ```

- [ ] **Configure Approved Domains**: Consider creating an approved domain list specifically for your region/country
  ```python
  # Add to settings.py
  APPROVED_HEALTHCARE_DOMAINS = [
      'hospital.org', 
      'healthcare.gov', 
      'medical-center.net',
      # Add country/region specific healthcare domains
  ]
  ```

## 2. Security Configuration

Production environments require additional security hardening.

### Required Actions:

- [ ] **Enable HTTPS**: Configure SSL/TLS for all authentication endpoints
  ```python
  # settings.py
  SECURE_SSL_REDIRECT = True
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  ```

- [ ] **Configure Rate Limiting**: Implement API rate limiting to prevent brute force attacks
  ```python
  # Add to settings.py (if using Django REST framework)
  REST_FRAMEWORK = {
      'DEFAULT_THROTTLE_CLASSES': [
          'rest_framework.throttling.AnonRateThrottle',
          'rest_framework.throttling.UserRateThrottle'
      ],
      'DEFAULT_THROTTLE_RATES': {
          'anon': '5/minute',
          'user': '20/minute',
          'hospital_admin_auth': '3/minute',  # Specific to admin login
      }
  }
  ```

- [ ] **Set Up IP Allowlisting**: Consider restricting admin access to known IP ranges
  ```python
  # Example middleware configuration
  ALLOWED_ADMIN_IPS = ['203.0.113.0/24', '198.51.100.0/24']
  ```

- [ ] **Enable Comprehensive Logging**: Configure detailed login attempt logging
  ```python
  # settings.py
  LOGGING = {
      'version': 1,
      'disable_existing_loggers': False,
      'handlers': {
          'file': {
              'level': 'INFO',
              'class': 'logging.FileHandler',
              'filename': '/var/log/django/hospital_admin_auth.log',
          },
          'security_file': {
              'level': 'WARNING',
              'class': 'logging.FileHandler',
              'filename': '/var/log/django/security.log',
          },
      },
      'loggers': {
          'api.views.auth.hospital_admin_auth': {
              'handlers': ['file', 'security_file'],
              'level': 'INFO',
              'propagate': True,
          },
      },
  }
  ```

## 3. Environment Setup

Configure production-specific settings.

### Required Actions:

- [ ] **Set DEBUG to False**: This activates strict validation rules
  ```python
  # settings.py
  DEBUG = False
  ```

- [ ] **Configure Production Email Service**: Set up a reliable email provider
  ```python
  # settings.py
  EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
  EMAIL_HOST = 'smtp.your-provider.com'
  EMAIL_PORT = 587
  EMAIL_USE_TLS = True
  EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
  EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
  DEFAULT_FROM_EMAIL = 'securelogin@healthcare-platform.org'
  ```

- [ ] **Set Up Secrets Management**: Use environment variables for sensitive data
  ```bash
  # Example .env file (use a secure method to manage in production)
  SECRET_KEY=your-secure-django-secret-key
  EMAIL_HOST_USER=your-email-service-username
  EMAIL_HOST_PASSWORD=your-email-service-password
  DATABASE_URL=your-database-connection-string
  ```

- [ ] **Configure Cache for OTP Storage**: Set up a reliable production cache
  ```python
  # settings.py
  CACHES = {
      'default': {
          'BACKEND': 'django.core.cache.backends.redis.RedisCache',
          'LOCATION': 'redis://redis:6379/1',
          'TIMEOUT': 600,  # 10 minutes for 2FA codes
      }
  }
  ```

## 4. Data Migration

Safely transition data from development to production.

### Required Actions:

- [ ] **Run Hospital Admin Email Migration Script**
  ```bash
  # Create and run a migration script that:
  # 1. Updates existing admin emails to official healthcare domains
  # 2. Validates all hospital registration codes
  # 3. Ensures user-hospital admin linkage is correct
  python manage.py migrate_hospital_emails --production
  ```

- [ ] **Reset Development Passwords**
  ```python
  # Create a script to force password reset for all hospital admins
  from django.contrib.auth.hashers import make_password
  from api.models.medical.hospital_auth import HospitalAdmin
  from api.models import CustomUser
  
  # Set temporary secure passwords and require reset
  for admin in HospitalAdmin.objects.all():
      if admin.user:
          admin.user.password = make_password(f"Secure{secrets.token_hex(8)}")
          admin.user.password_reset_required = True
          admin.user.save()
  ```

- [ ] **Verify Hospital Registration Numbers**: Ensure all hospitals have valid, unique codes
  ```sql
  -- Check for duplicate or missing registration numbers
  SELECT registration_number, COUNT(*) 
  FROM api_hospital 
  GROUP BY registration_number 
  HAVING COUNT(*) > 1 OR registration_number IS NULL;
  ```

## 5. Administrator Communication

Prepare administrators for the transition.

### Required Actions:

- [ ] **Create Announcement Email**: Notify all hospital admins about the new system
  ```
  Subject: Important Security Update - New Hospital Admin Login System
  
  Dear [Hospital Name] Administrator,
  
  On [Go-Live Date], we will be implementing a new secure login system for all hospital administrators. This system includes:
  
  1. A dedicated hospital administrator login portal
  2. Two-factor authentication for all logins
  3. Hospital code verification
  
  Your hospital registration code is: [Hospital Code]
  
  Please keep this code confidential as it will be required for all future logins.
  
  Additional details and training materials are available at: [Support URL]
  ```

- [ ] **Create User Guide**: Develop documentation for the new login flow
  ```
  # Hospital Administrator Login Guide
  
  ## Logging In
  1. Visit [Admin Portal URL]
  2. Enter your official hospital email
  3. Enter your password
  4. Enter your hospital registration code
  5. Check your email for a verification code
  6. Enter the code to complete login
  
  ## Security Tips
  - Never share your hospital registration code
  - Two-factor authentication codes expire after 10 minutes
  - Report suspicious login attempts immediately
  ```

- [ ] **Schedule Training Sessions**: Plan for admin orientation to the new system

## 6. Verification Process

Fine-tune the verification parameters for production.

### Required Actions:

- [ ] **Adjust OTP Expiry Time**: Set appropriate expiration times
  ```python
  # In hospital_admin_auth.py
  # Change 600 (10 minutes) to desired expiry time in seconds
  cache.set(cache_key, {
      'code': verification_code,
      'secret': totp_secret,
      'timestamp': timezone.now().timestamp(),
      'attempts': 0
  }, timeout=600)  # Production timeout
  ```

- [ ] **Configure Trusted Device Duration**: Set appropriate remembered device duration
  ```python
  # If remember device is set, store a trusted device token
  if remember_device and device_id:
      trusted_device_key = f"trusted_device_{user.id}_{device_id}"
      trusted_token = secrets.token_hex(32)
      # Store for 30 days (adjust as needed)
      cache.set(trusted_device_key, trusted_token, timeout=60*60*24*30)
  ```

- [ ] **Update Email Templates**: Finalize production email templates
  ```html
  <!-- Update branding, contact information, and security messaging -->
  <!-- Ensure all URLs point to production domains -->
  ```

## 7. Monitoring & Support

Establish monitoring and support processes.

### Required Actions:

- [ ] **Set Up Login Monitoring**: Configure alerts for suspicious activities
  ```python
  # Example alert for multiple failed login attempts
  if cached_data['attempts'] > 3:
      send_security_alert(
          admin_email=email,
          hospital_id=hospital.id,
          alert_type='excessive_failed_attempts',
          ip_address=get_client_ip(request)
      )
  ```

- [ ] **Create Admin Support Channel**: Establish dedicated support for hospital admins
  ```
  # Support Protocol
  Support Email: hospital-admin-support@healthcare-platform.org
  Support Phone: +1-800-555-HELP
  Emergency Contact: security-team@healthcare-platform.org
  ```

- [ ] **Implement Audit Logging**: Set up comprehensive logging for compliance
  ```python
  # Add to hospital_admin_auth.py
  logger.info(
      f"ADMIN_LOGIN: user={user.id} hospital={hospital.id} ip={get_client_ip(request)} "
      f"success={success} timestamp={timezone.now().isoformat()}"
  )
  ```

## 8. Testing Checklist

Verify all aspects of the system before go-live.

### Required Actions:

- [ ] **Complete End-to-End Testing**: Test the full login flow in production-like environment
  - [ ] Login with valid credentials
  - [ ] Login with invalid credentials
  - [ ] Password reset flow
  - [ ] 2FA timeout and resend
  - [ ] Remember device functionality

- [ ] **Security Testing**: Conduct penetration testing on authentication endpoints
  - [ ] Brute force protection
  - [ ] Rate limiting effectiveness
  - [ ] Session management security
  - [ ] Cross-site request forgery protection

- [ ] **Email Delivery Testing**: Verify email templates in various clients
  - [ ] Gmail, Outlook, Apple Mail
  - [ ] Mobile email clients
  - [ ] Email delivery speed and reliability

- [ ] **Browser Compatibility**: Test across multiple browsers and devices
  - [ ] Chrome, Firefox, Safari, Edge
  - [ ] Mobile devices
  - [ ] Tablets

## 9. Rollback Plan

Prepare for contingencies.

### Required Actions:

- [ ] **Create Database Backup**: Before migration, create full database backup
  ```bash
  pg_dump healthcare_db > healthcare_db_pre_migration.sql
  ```

- [ ] **Prepare Rollback Script**: Create script to revert to old system if needed
  ```python
  # rollback_hospital_admin_migration.py
  # Script to restore previous login flow if severe issues are encountered
  ```

- [ ] **Define Go/No-Go Criteria**: Establish clear criteria for proceeding with launch

- [ ] **Schedule Deployment Window**: Plan for off-peak deployment time
  ```
  Recommended Deployment Window: Sunday, 01:00 - 05:00
  ```

---

## Additional Resources

- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [HIPAA Security Compliance Guidelines](https://www.hhs.gov/hipaa/for-professionals/security/index.html)

---

Document Version: 1.0  
Last Updated: May 13, 2025  
Author: PHB Healthcare Platform Implementation Team
