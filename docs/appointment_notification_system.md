# Appointment Notification System Documentation

## Overview

The PHB system has two notification mechanisms for appointments:

1. **Direct Email Sending**: Functions in `api/utils/email.py` that directly send emails using Django's email functionality.
2. **Database-backed Notification System**: The `AppointmentNotification` model that stores notifications in the database and can send them either immediately or at scheduled times.

## Current Implementation

We've updated the system to ensure immediate notification delivery when appointments are created:

1. Notifications are created in the `AppointmentSerializer.create()` method
2. They are immediately sent using the `notification.send()` method
3. Future reminders are scheduled for delivery closer to the appointment date

## Notification Types

The system supports multiple notification channels:

- Email notifications
- SMS notifications
- In-app notifications
- WhatsApp notifications (planned for future)

## How the Database-backed System Works

1. **Creation**: When events occur (like booking an appointment, rescheduling, or cancellation), notification records are created in the database through the `AppointmentNotification` model.

2. **Delivery**: Notifications can be delivered in two ways:
   - **Immediate delivery**: Using the `notification.send()` method right after creation
   - **Scheduled delivery**: Processed by the `process_pending_notifications` management command when their scheduled time arrives

3. **Status Tracking**: After processing, notifications are marked as 'sent' or 'failed', and failed notifications can be retried.

## Best Practices

For immediate notifications (like booking confirmations):
```python
# Create notification
notification = AppointmentNotification.create_booking_confirmation(appointment)

# Get all pending notifications for this appointment
notifications = AppointmentNotification.objects.filter(
    appointment=appointment,
    status='pending'
)

# Send them immediately
for notification in notifications:
    notification.send()
```

For scheduled notifications (like reminders):
```python
# Create reminder notifications
reminder_schedule = [
    {'days_before': 2, 'type': 'email'},
    {'days_before': 1, 'type': 'sms'},
    {'hours_before': 2, 'type': 'sms'}
]
AppointmentNotification.create_reminders(appointment, reminder_schedule)

# These will be sent later by the scheduled task
```

## Using `process_pending_notifications` Management Command

This command is still needed to process scheduled notifications that should be sent later:

```bash
# Process all pending notifications (up to 100 by default)
python3 manage.py process_pending_notifications

# Run in dry-run mode (show what would be sent without actually sending)
python3 manage.py process_pending_notifications --dry-run

# Also retry failed notifications (within retry limits)
python3 manage.py process_pending_notifications --retry-failed

# Process only a specific number of notifications
python3 manage.py process_pending_notifications --max 10
```

## Setting up Automated Processing

To ensure scheduled notifications are sent automatically, set up a cron job or scheduled task:

```bash
# Run every 5 minutes
*/5 * * * * cd /path/to/project && python3 manage.py process_pending_notifications --max 100
```

## Email Templates

Email notifications use HTML templates located in:
- `api/templates/email/`

The system will try to find templates in:
- `notifications/email/[template_name].html`
- And if not found, fall back to:
- `email/[template_name].html`

## Checking Notification Status

You can run this test script to check for pending notifications:

```bash
python3 api/tests/check_pending_notifications.py
```

## Advantages of the Database-backed System

1. **Reliable delivery**: Even if the immediate send fails, the notification remains in the system
2. **Retry capabilities**: Failed notifications can be retried automatically
3. **Scheduled notifications**: Support for future-dated notifications like reminders
4. **Multi-channel support**: Single API for email, SMS, in-app, WhatsApp
5. **Tracking and analytics**: Can track open rates, delivery status, etc.
6. **Centralized template management**: Uses Django templates for consistent messaging

## SMS Notifications

Currently, SMS notifications may fail if:
1. The user doesn't have a phone number
2. The Twilio configuration is not set up correctly

If SMS notifications are critical, ensure that:
1. User phone numbers are captured and validated
2. Twilio settings (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER) are configured in settings

## Future Improvements

For future enhancements, consider:

1. **Consolidating the notification systems** - Either use only the direct email methods or only the database-backed notification system
2. **Better error handling** - Add more specific error messages and recovery options
3. **Admin monitoring interface** - Create a Django admin view to monitor notification status
4. **Webhook callbacks** - Implement delivery receipt tracking for SMS notifications
5. **Notification preferences** - Allow users to set their notification preferences (email, SMS, etc.) 