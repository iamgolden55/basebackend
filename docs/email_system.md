# Email System Documentation

## Overview

The email system handles all email communications in the application, with a focus on appointment-related notifications. It uses Django's email backend with HTML templates for consistent, professional communications.

## Components

### 1. Email Backend Configuration

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.your-email-provider.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@domain.com'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
```

### 2. Email Templates

Located in `api/templates/email/`:

```
email/
├── base.html                           # Base template
├── appointment/
│   ├── booking_confirmation.html       # New booking
│   ├── reminder.html                   # Appointment reminder
│   ├── cancellation.html              # Appointment cancelled
│   ├── rescheduled.html              # Time/date changed
│   ├── completion.html               # After appointment
│   └── emergency.html                # Urgent updates
├── payment/
│   ├── confirmation.html             # Payment received
│   └── reminder.html                 # Payment needed
└── doctor/
    ├── new_appointment.html          # New appointment
    ├── cancellation.html            # Patient cancelled
    └── emergency.html               # Emergency case
```

### 3. Base Template

```html
<!-- base.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{% endblock %}</title>
    <style>
        /* Common styles */
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #666;
        }
        .button {
            display: inline-block;
            padding: 10px 20px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{% block header %}{% endblock %}</h1>
        </div>
        
        <div class="content">
            {% block content %}{% endblock %}
        </div>
        
        <div class="footer">
            <p>This is an automated message from Your Hospital Name</p>
            <p>Please do not reply to this email</p>
        </div>
    </div>
</body>
</html>
```

### 4. Email Service

```python
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

class EmailService:
    @staticmethod
    def send_email(template_name, context, subject, recipient_list):
        """
        Sends an HTML email using a template.
        
        Args:
            template_name: Path to template
            context: Template context
            subject: Email subject
            recipient_list: List of recipients
        """
        # Render HTML content
        html_content = render_to_string(f'email/{template_name}', context)
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list
        )
        
        # Attach HTML content
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        try:
            email.send()
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
```

### 5. Appointment Notifications

```python
class AppointmentEmailService:
    @staticmethod
    def send_booking_confirmation(appointment):
        """Sends booking confirmation email to patient and doctor."""
        # Patient notification
        context = {
            'patient_name': appointment.patient.get_full_name(),
            'doctor_name': appointment.doctor.get_full_name(),
            'appointment_date': appointment.appointment_date,
            'appointment_time': appointment.appointment_time,
            'department': appointment.department.name,
            'appointment_type': appointment.get_appointment_type_display(),
            'hospital_name': appointment.hospital.name,
            'hospital_address': appointment.hospital.address,
        }
        
        EmailService.send_email(
            template_name='appointment/booking_confirmation.html',
            context=context,
            subject='Appointment Confirmation',
            recipient_list=[appointment.patient.email]
        )
        
        # Doctor notification
        doctor_context = {
            'patient_name': appointment.patient.get_full_name(),
            'appointment_date': appointment.appointment_date,
            'appointment_time': appointment.appointment_time,
            'appointment_type': appointment.get_appointment_type_display(),
            'symptoms': appointment.symptoms
        }
        
        EmailService.send_email(
            template_name='doctor/new_appointment.html',
            context=doctor_context,
            subject='New Appointment Scheduled',
            recipient_list=[appointment.doctor.email]
        )
    
    @staticmethod
    def send_reminder(appointment, days_before):
        """Sends reminder email to patient."""
        context = {
            'patient_name': appointment.patient.get_full_name(),
            'doctor_name': appointment.doctor.get_full_name(),
            'appointment_date': appointment.appointment_date,
            'appointment_time': appointment.appointment_time,
            'days_before': days_before,
            'hospital_name': appointment.hospital.name,
            'hospital_address': appointment.hospital.address,
        }
        
        EmailService.send_email(
            template_name='appointment/reminder.html',
            context=context,
            subject=f'Appointment Reminder - {days_before} days to go',
            recipient_list=[appointment.patient.email]
        )
```

## Best Practices

### 1. Template Design
- Use responsive design
- Keep content clear and concise
- Include all necessary information
- Use consistent branding
- Test across email clients

### 2. Content Guidelines
- Clear subject lines
- Important info at the top
- Call-to-action buttons
- Contact information
- Unsubscribe option

### 3. Technical Considerations
- Use inline CSS
- Test with different devices
- Handle bounces and failures
- Track delivery status
- Implement rate limiting

### 4. Security
- Use TLS encryption
- Validate email addresses
- Protect sensitive data
- Monitor for abuse
- Regular security audits

## Error Handling

### 1. Delivery Failures
```python
def handle_delivery_failure(email, error):
    """
    Handles email delivery failures.
    
    Args:
        email: Failed email object
        error: Error details
    """
    # Log the error
    logger.error(f"Email delivery failed: {str(error)}")
    
    # Create failure record
    EmailDeliveryFailure.objects.create(
        recipient=email.to[0],
        subject=email.subject,
        error_message=str(error)
    )
    
    # Retry if appropriate
    if should_retry(error):
        schedule_retry(email)
```

### 2. Retry Mechanism
```python
def schedule_retry(email, attempt=1):
    """
    Schedules a retry for failed email.
    
    Args:
        email: Failed email object
        attempt: Current attempt number
    """
    if attempt <= 3:  # Max 3 attempts
        delay = 2 ** attempt  # Exponential backoff
        send_email_task.apply_async(
            args=[email],
            countdown=delay * 60  # Convert to minutes
        )
```

## Monitoring

### 1. Email Metrics
- Delivery rate
- Open rate
- Bounce rate
- Click-through rate
- Response time

### 2. Performance Monitoring
```python
def track_email_metrics(email):
    """
    Tracks email performance metrics.
    
    Args:
        email: Sent email object
    """
    EmailMetrics.objects.create(
        recipient=email.to[0],
        subject=email.subject,
        sent_at=timezone.now(),
        delivery_status='sent'
    )
```

## Integration Points

### 1. SMS Gateway
- Fallback for urgent notifications
- Delivery confirmation
- Status updates

### 2. Notification Service
- Coordinate with other channels
- Manage user preferences
- Handle rate limiting

### 3. Template System
- Dynamic content insertion
- Localization support
- Version control

## Testing

### 1. Unit Tests
```python
def test_email_sending():
    """Tests email sending functionality."""
    email = EmailService.send_email(
        template_name='test.html',
        context={'test': 'data'},
        subject='Test Email',
        recipient_list=['test@example.com']
    )
    assert email.status == 'sent'
```

### 2. Template Tests
```python
def test_template_rendering():
    """Tests template rendering."""
    context = {'name': 'Test User'}
    html = render_to_string('email/test.html', context)
    assert 'Test User' in html
``` 