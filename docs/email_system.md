# PHB Email System Documentation

## Overview
The PHB (Public Health Bureau) email system handles various types of automated emails sent to users throughout their interaction with the platform. The system is designed to be reliable, informative, and maintain a consistent brand identity.

## Email Types

### 1. Verification Email
Sent immediately after user registration to verify the user's email address.

**When it's sent:**
- After successful user registration
- When user requests email verification resend

**Content:**
- Verification link
- Welcome message
- Instructions for verification
- Security notice

### 2. Welcome Email 🎉
Sent after successful email verification, providing users with their account details and system information.

**When it's sent:**
- Immediately after successful email verification

**Content:**
- Personal greeting
- Account Information:
  - Full Name
  - Healthcare Provider Number (HPN)
  - Email Address
  - Phone Number (if provided)
  - Location Details
- System Features Overview:
  - Health records access
  - Appointment scheduling
  - Health notifications
  - Healthcare facility connections
  - Medical history tracking
- Quick access links:
  - Dashboard
  - Help Center
  - Support Contact

### 3. Password Reset Email
Sent when users request to reset their password.

**When it's sent:**
- When user initiates password reset
- Contains security information about the request

**Content:**
- Reset password link
- Security information:
  - Request location
  - Device information
  - IP address
  - Timestamp

## Technical Implementation

### Email Templates
All email templates are located in `api/templates/email/`:
- `verification.html`: Email verification template
- `welcome.html`: Welcome email template
- `reset-password.html`: Password reset template
- `verification_result.html`: Verification result page

### Utility Functions
Located in `api/utils/email.py`:

```python
def send_welcome_email(user):
    """
    Sends welcome email to newly verified users
    Returns: Boolean indicating success/failure
    """

def send_verification_email(user, verification_link):
    """
    Sends verification email to new users
    Returns: Boolean indicating success/failure
    """
```

### Environment Variables Required
```
NEXTJS_URL=<frontend_url>
SERVER_API_URL=<backend_url>
DEFAULT_FROM_EMAIL=<sender_email>
```

## Email Design Guidelines

### Visual Elements
- PHB logo and branding
- Consistent color scheme
- Responsive design for all devices
- Clear call-to-action buttons

### Content Guidelines
- Clear and concise messaging
- Professional yet friendly tone
- Important information highlighted
- Action items clearly visible

### Security Features
- Tokens expire after 24 hours
- Location tracking for password resets
- Device information included
- Non-reusable verification links

## Error Handling

### Logging
All email-related activities are logged:
- Successful sends
- Failed attempts
- Verification attempts
- Welcome email status

### Error Responses
The system provides clear error messages for:
- Invalid tokens
- Expired links
- Failed email sends
- Server errors

## Best Practices

1. **Email Sending**
   - Use non-blocking async operations
   - Implement retry mechanism
   - Monitor delivery rates
   - Handle bounces appropriately

2. **Security**
   - Use secure tokens
   - Include IP and device info
   - Implement rate limiting
   - Follow HIPAA guidelines

3. **Content**
   - Mobile-responsive design
   - Alt text for images
   - Plain text alternatives
   - Clear call-to-actions

## Testing

### Test Cases
- Verification email delivery
- Welcome email content
- Password reset functionality
- Token expiration
- Error handling
- Email template rendering

### Test Environment
- Use test email service
- Verify all links
- Check responsive design
- Validate content

## Maintenance

### Regular Tasks
- Monitor email delivery rates
- Update templates as needed
- Check for bounced emails
- Update security measures
- Review and update content

### Troubleshooting
- Check logs for errors
- Verify environment variables
- Test email service connection
- Validate email templates

## Future Improvements

Planned enhancements:
- Email preference management
- Additional language support
- Enhanced analytics
- A/B testing capability
- Automated retry system 