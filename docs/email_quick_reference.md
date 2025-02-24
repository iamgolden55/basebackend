# PHB Email System - Quick Reference Guide

## 🚀 Quick Start

### Sending Emails

```python
from api.utils.email import send_verification_email, send_welcome_email

# Send verification email
send_verification_email(user, verification_link)

# Send welcome email
send_welcome_email(user)
```

## 📧 Email Templates Location
```
api/templates/email/
├── verification.html      # New user verification
├── welcome.html          # Post-verification welcome
├── reset-password.html   # Password reset
└── verification_result.html  # Verification result page
```

## 🔑 Required Environment Variables
```bash
NEXTJS_URL="http://localhost:3000"  # Frontend URL
SERVER_API_URL="http://localhost:8000"  # Backend URL
DEFAULT_FROM_EMAIL="noreply@phb.com"  # Sender email
```

## 📝 Email Types & When to Use

### 1. Verification Email
```python
# When registering a new user
user.email_verification_token = uuid.uuid4()
user.save()
verification_link = f"{os.environ.get('SERVER_API_URL')}api/email/verify/{user.email_verification_token}/"
send_verification_email(user, verification_link)
```

### 2. Welcome Email
```python
# After email verification
user.is_email_verified = True
user.save()
send_welcome_email(user)
```

### 3. Password Reset
```python
# In password reset view
token = secrets.token_urlsafe(32)
user.password_reset_token = token
user.save()
context = {
    'reset_link': f"{os.environ.get('NEXTJS_URL')}/auth/reset-password?token={token}",
    'user_name': user.first_name,
    # ... other context data
}
```

## 🔍 Error Handling

### Check Email Status
```python
email_sent = send_welcome_email(user)
if not email_sent:
    logger.error(f"Failed to send welcome email to {user.email}")
```

### Common Error Responses
```python
# Email sending failed
Response({
    'status': 'error',
    'message': 'Failed to send email',
    'detail': str(e) if settings.DEBUG else 'Please try again later.'
}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Invalid token
Response({
    'error': 'Invalid or expired token'
}, status=status.HTTP_400_BAD_REQUEST)
```

## 📋 Template Context Examples

### Welcome Email
```python
context = {
    'user': user,  # User object with all details
    'frontend_url': frontend_url  # Frontend URL for links
}
```

### Password Reset
```python
context = {
    'reset_link': reset_link,
    'user_name': user.first_name,
    'country': location_info.get('country'),
    'city': location_info.get('city'),
    'ip_address': request.META.get('REMOTE_ADDR'),
    'device': request.META.get('HTTP_USER_AGENT'),
    'date': timezone.now().strftime('%b %d %Y %H:%M:%S %Z')
}
```

## 🐛 Debug Tips

### Check Email Logs
```python
logger.info(f"Welcome email {'sent successfully' if welcome_email_sent else 'failed to send'} for user: {user.email}")
```

### Test Email Configuration
```python
from django.core.mail import send_mail
try:
    send_mail(
        subject='Test Email',
        message='This is a test',
        from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
        recipient_list=['test@example.com'],
        fail_silently=False,
    )
except Exception as e:
    print(f"Email configuration error: {str(e)}")
```

## 🔒 Security Best Practices

1. Always use `uuid.uuid4()` for verification tokens
2. Use `secrets.token_urlsafe()` for password reset tokens
3. Include IP and device info in security-sensitive emails
4. Implement rate limiting for email sending
5. Never expose email templates publicly

## 📚 Related Documentation
- [Full Email System Documentation](email_system.md)
- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
- [Security Guidelines](security.md) 