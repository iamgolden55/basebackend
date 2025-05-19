# PHB Hospital Admin Authentication System

*Last Updated: May 14, 2025*

## Table of Contents

1. [Overview](#overview)
2. [Security Features](#security-features)
3. [Hospital Admin Creation Process](#hospital-admin-creation-process)
4. [Login Flow](#login-flow)
5. [Secure Password Reset Flow](#secure-password-reset-flow)
6. [Email Communications](#email-communications)
7. [Technical Implementation](#technical-implementation)
8. [Future Improvements](#future-improvements)

## Overview

The PHB Hospital Admin Authentication System provides a secure, robust way for hospital administrators to access the Public Health Bureau platform. This system includes multiple layers of security while maintaining usability for hospital staff.

## Security Features

### 1. Secure Admin Username Format

Rather than using real email addresses for admin logins, the system generates standardized PHB usernames in the format:

- Development mode: `admin.hospitalname@example.com`
- Production mode: `admin.hospitalname@phb.com`

This approach enhances security by:
- Making admin usernames harder to guess
- Separating login credentials from communication channels
- Creating a clear distinction between system access and email communications
- Standardizing admin account identification

### 2. Multi-Factor Authentication (MFA)

All hospital admin accounts require 2FA verification:

- Time-based One-Time Password (TOTP) system
- Verification codes sent to the admin's real contact email
- Configurable validation window (narrower in production, wider in development)
- Intelligent fallback system for determining the best contact email

### 3. Advanced Rate Limiting

```python
class HospitalAdminLoginRateThrottle(AnonRateThrottle):
    """Rate limiting for hospital admin login attempts."""
    scope = 'hospital_admin_login'
    rate = '5/minute'  # Stricter rate limiting for admin access

class HospitalAdmin2FARateThrottle(AnonRateThrottle):
    """Rate limiting for 2FA verification attempts."""
    scope = 'hospital_admin_2fa'
    rate = '3/minute'  # Very strict rate for 2FA attempts
```

### 4. Account Lockout Protection

- IP-based rate limiting after 3 failed attempts
- Account lockout for 15 minutes after 5 failed attempts
- Email alerts sent after 3 failed login attempts
- Password reset unlocking: Account lockout is automatically cleared after successful password reset
- Comprehensive security logging for authentication attempts

### 5. Required Password Change on First Login

- New administrators must change their auto-generated password
- Password complexity requirements with minimum strength standards
- Password change history tracking

### 6. Hospital Code Verification

- Three-factor authentication requiring:
  1. Admin username
  2. Password
  3. Hospital registration code

### 7. Comprehensive Security Audit Logging

```python
log_data = {
    'timestamp': timezone.now().isoformat(),
    'action': action_type,
    'ip_address': ip_address,
    'user_agent': user_agent,
    'email': email,
    'location': location_info,
    'status': status,
    'response_code': response_code,
    'duration_ms': duration_ms
}
```

## Hospital Admin Creation Process

### Automatic Account Creation

When a new hospital is registered:

1. The system automatically creates a hospital admin account using:
   - A standardized PHB username (`admin.hospitalname@phb.com`)
   - The real contact email for communications
   - A securely generated password (in production) or a development default

2. The `HospitalAdmin` model links:
   - The associated `CustomUser` account
   - The hospital registration
   - Contact information
   - Password management settings

### Code Implementation

```python
# Generate standardized PHB admin username
if settings.DEBUG:
    # Development format - using example.com domain
    admin_username = f"admin.{hospital.name.lower().replace(' ', '')}@example.com"
    admin_password = "Password123!"
else:
    # Production format - using phb.com domain
    admin_username = f"admin.{hospital.name.lower().replace(' ', '')}@phb.com"
    admin_password = generate_secure_password()
```

## Login Flow

1. **Initial Login Screen**
   - User enters:
     - Hospital code (format: H-XXXXXXXX)
     - Admin username (format: admin.hospitalname@phb.com)
     - Password

2. **Authentication & Validation**
   - System verifies the hospital code against registered hospitals
   - Validates the admin username and password
   - Confirms the admin is authorized for the specified hospital

3. **2FA Verification**
   - System generates a time-based one-time password (TOTP)
   - Code is sent to the admin's real contact email (not the PHB username)
   - Intelligent email resolution to ensure codes are sent to valid inboxes
   - User must enter the verification code to complete login

4. **Post-Authentication**
   - First-time login requires password change
   - JWT tokens issued for authorized session
   - Access granted to hospital admin dashboard

## Secure Password Reset Flow

### 1. Multi-factor Identity Verification

The enhanced password reset process requires multiple verification factors:

1. **Initial Request**
   - Admin initiates password reset via dedicated secure portal
   - Required fields:
     - Hospital admin email
     - Hospital registration code
   - System captures device fingerprint and IP address for security audit

2. **Primary Verification**
   - System sends a 6-digit verification code to the admin's registered contact email
   - Limited validity period (30 minutes)
   - Includes visual security indicators and warnings

3. **Secondary Verification**
   - After email verification, additional verification may be required
   - Hospital code re-confirmation
   - Recognition of previous login location/details
   - Device trust assessment

4. **Security Notifications**
   - Real-time alerts sent to IT security team when reset is initiated
   - Complete audit trail maintained for forensic analysis
   - Final confirmation emails after successful reset

### 2. Reset Process Security Features

```python
class HospitalAdminResetRequestThrottle(AnonRateThrottle):
    """Rate limiting for hospital admin password reset requests."""
    scope = 'hospital_admin_reset_request'
    rate = '3/hour'  # Very strict rate limiting for reset requests

class HospitalAdminResetVerifyThrottle(AnonRateThrottle):
    """Rate limiting for reset verification attempts."""
    scope = 'hospital_admin_reset_verify'
    rate = '5/hour'  # Strict rate limiting for verification attempts
```

- **Time-limited Reset Window**: 30-minute maximum window to complete the process
- **Device Fingerprinting**: Additional trust for resets from previously trusted devices
- **Failed Attempt Protection**: Reset process invalidated after 3 failed verification attempts
- **Automatic 2FA Enforcement**: Next login after reset requires 2FA authentication
- **Password History Check**: Prevention of password reuse

### 3. Technical Implementation Flow

1. **Request Initiation** (`/hospitals/admin/reset-password/request/`)
   - Validates hospital code against admin email
   - Generates secure tokens for multi-step verification
   - Stores reset metadata (IP, device, timestamp) for audit
   - Sends secure verification code via email

2. **Verification** (`/hospitals/admin/reset-password/verify/`)
   - Validates the verification code from email
   - Performs additional identity checks
   - Validates the request hasn't expired (30-minute window)
   - Issues secondary token for final completion step

3. **Reset Completion** (`/hospitals/admin/reset-password/complete/`)
   - Validates both primary and secondary tokens
   - Enforces secure password requirements
   - Updates password with comprehensive audit trail
   - Sends confirmation notifications to admin and security team
   - Clears any account lockouts

## Email Communications

### 1. Welcome Email

Sent when a hospital admin account is created:
- Clear distinction between login username and contact email
- Hospital code for authentication
- Initial password (if system-generated)
- Instructions for first login and password change

### 2. Password Reset Emails

Multiple secure communications for password reset:

- **Password Reset Request Email**
  - 6-digit verification code
  - Secure reset link
  - Security warnings and expiration details
  - Clear visual security indicators

- **Reset Confirmation Email**
  - Confirmation of successful password change
  - Details of the reset (time, location, device)
  - Instructions for reporting unauthorized changes
  - Security reminders for next login

- **Security Team Notifications**
  - Alert when reset is initiated
  - Complete details of reset request (location, device, time)
  - Final notification when reset is completed
  - Includes full audit information

### 3. Security Alert Emails

Sent on suspicious activity:
- Failed login attempts
- Account lockouts
- Password reset requests
- New device logins
- Multiple verification failures

## Technical Implementation

### Database Structure

#### HospitalAdmin Model

```python
class HospitalAdmin(models.Model):
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE)
    hospital = models.ForeignKey('Hospital', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    email = models.EmailField(unique=True, 
        help_text="The admin username used for login (not a real email inbox)")
    contact_email = models.EmailField(null=True, blank=True, 
        help_text="The real email address for communications")
    password = models.CharField(max_length=128)  # To be removed later
    password_change_required = models.BooleanField(default=True, 
        help_text="Whether the admin must change their password on next login")
    last_password_change = models.DateTimeField(null=True, blank=True, 
        help_text="When the admin last changed their password")
    created_at = models.DateTimeField(default=timezone.now)
```

### 2FA Code Generation & Verification

```python
# Generate TOTP code
totp_secret = pyotp.random_base32()
totp = pyotp.TOTP(totp_secret)
verification_code = totp.now()

# Verify code (production mode)
if not totp.verify(verification_code, valid_window=1):
    return Response({
        "status": "error",
        "message": "Invalid verification code. Please try again."
    }, status=status.HTTP_400_BAD_REQUEST)
```

### Intelligent Email Resolution

```python
# Use real contact email if available, otherwise try other methods to find it
if admin.contact_email:
    # Preferred: Use the dedicated contact_email field
    contact_email = admin.contact_email
    logger.info(f"Using contact_email field for 2FA: {contact_email}")
elif admin.hospital.email:
    # Option 2: Try the hospital email if that's meant to reach the admin
    contact_email = admin.hospital.email
    logger.info(f"Using hospital email for 2FA: {contact_email}")
elif authenticated_user.email != email:
    # Option 3: If the user object email is different from the login username, use that
    contact_email = authenticated_user.email
    logger.info(f"Using authenticatedUser.email for 2FA: {contact_email}")
else:
    # Last resort: Use the admin username (not ideal if it's not a real inbox)
    contact_email = email
    logger.warning(f"FALLBACK: Using admin username as email for 2FA: {contact_email}")
```

## Future Improvements

### 1. Enhanced Authentication Options

- **WebAuthn/FIDO2 Support**: Add support for security keys and biometric authentication
- **Authenticator App Integration**: Allow admins to use apps like Google Authenticator instead of email-based OTP
- **SMS Verification Option**: Add phone number verification as an alternative to email
- **Trusted Device Management**: Allow admins to manage and revoke trusted devices

### 2. Security Enhancements

- **Risk-Based Authentication**: Adjust security requirements based on risk factors (location, device, time of day)
- **Adaptive Challenge Questions**: Implement secondary verification for unusual login patterns
- **IP Reputation Checking**: Block login attempts from known malicious IP addresses
- **Session Timeout Controls**: Configurable session duration based on hospital policy
- **Login Anomaly Detection**: AI-based system to detect unusual login patterns

### 3. Administrative Improvements

- **Self-Service Portal**: Allow admins to manage their security settings, devices, and contact information
- **Admin Access Delegation**: Enable temporary account access with limited permissions
- **Role-Based Access Controls**: More granular permissions within hospital admin accounts
- **Audit Log Dashboard**: Visual interface for reviewing security events
- **Emergency Access Protocol**: Define procedures for emergency access when primary admins are unavailable

### 4. Technical Enhancements

- **Hardware Security Module (HSM) Integration**: Store cryptographic keys in dedicated hardware
- **Zero-Knowledge Proof Verification**: Enhance privacy in the authentication process
- **OAuth/OpenID Integration**: Support for enterprise identity providers
- **Password-less Authentication Options**: Email magic links or push notifications
- **Encrypted Credential Storage**: Additional encryption layer for sensitive user data
- **Enhanced Password Reset Flow**: Further improvements to the multi-step verification process

### 5. Usability Improvements

- **Customizable Security Policies**: Allow hospital systems to define their own security requirements
- **Progressive Security Enrollment**: Guide new admins through security setup in manageable steps
- **Localized Authentication Experience**: Adapt the login flow to regional preferences and languages
- **Accessibility Enhancements**: Ensure authentication flows work with assistive technologies
- **Visual Security Indicators**: Clear visual feedback about security status and requirements

### 6. Compliance & Auditing

- **Compliance Reporting**: Generate reports for HIPAA, GDPR, and other regulatory frameworks
- **Security Certifications**: Streamline SOC2, HITRUST, and similar certification processes
- **Penetration Testing Framework**: Built-in tools for regular security assessments
- **Security Posture Scoring**: Automated evaluation of implementation security
- **Detailed Access Logs**: Enhanced logging for medical record access and changes

---

*This documentation is confidential and proprietary to Public Health Bureau (PHB).*
