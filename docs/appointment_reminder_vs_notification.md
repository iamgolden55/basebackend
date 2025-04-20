# AppointmentReminder vs AppointmentNotification

## Key Differences

### 1. Purpose
**AppointmentReminder**
- Specifically for scheduling and managing reminders
- Focuses on time-based notifications before appointments
- Handles retry logic and delivery tracking
- Manages multiple reminder schedules per appointment

**AppointmentNotification**
- General notification system for all appointment-related communications
- Handles all types of notifications (not just reminders)
- Manages templates and multi-channel delivery
- Deals with immediate and scheduled notifications

### 2. Features Comparison

| Feature | AppointmentReminder | AppointmentNotification |
|---------|-------------------|----------------------|
| Primary Focus | Time-based reminders | All appointment communications |
| Scheduling | Complex scheduling with retry logic | Basic scheduling |
| Tracking | Detailed delivery tracking | Basic delivery status |
| Templates | Basic message templates | Full HTML email templates |
| Use Cases | Pre-appointment reminders | All appointment events |

### 3. When to Use Each

**Use AppointmentReminder when:**
```python
# Creating scheduled reminders
reminder_schedule = [
    {'days_before': 7, 'type': 'email'},  # 1 week before
    {'days_before': 2, 'type': 'email'},  # 2 days before
    {'days_before': 1, 'type': 'sms'},    # 1 day before
    {'hours_before': 2, 'type': 'sms'}    # 2 hours before
]

AppointmentNotification.create_reminders(appointment, reminder_schedule)
```

**Use AppointmentNotification when:**
```python
# Sending immediate notifications
# For patient
AppointmentNotification.objects.create(
    appointment=appointment,
    recipient=appointment.patient,
    notification_type='email',
    event_type='booking_confirmation',
    subject='Appointment Confirmation',
    message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} has been scheduled.',
    scheduled_time=timezone.now()
)

# For doctor
AppointmentNotification.objects.create(
    appointment=appointment,
    recipient=appointment.doctor.user,
    notification_type='email',
    event_type='booking_confirmation',
    subject='New Appointment',
    message=f'New appointment scheduled with {appointment.patient.get_full_name()}.',
    scheduled_time=timezone.now()
)
```

### 4. Key Methods

**AppointmentReminder Methods:**
```python
reminder.mark_as_sent()           # Track delivery
reminder.mark_as_failed()         # Handle failures
reminder.track_open()             # Track email opens
reminder.track_click()            # Track link clicks
reminder.calculate_next_retry_time()  # Manage retries
```

**AppointmentNotification Methods:**
```python
notification.send()               # Send notification
notification._send_email()        # Send email
notification._send_sms()          # Send SMS
notification._send_whatsapp()     # Send WhatsApp
notification._send_in_app()       # Send in-app notification
```

### 5. Data Model Differences

**AppointmentReminder Fields:**
```python
time_before_appointment  # Duration before appointment
scheduled_time          # When to send reminder
retry_count            # Number of retry attempts
next_retry_at          # Next retry timestamp
opened_at              # When reminder was opened
clicked_at             # When links were clicked
```

**AppointmentNotification Fields:**
```python
event_type             # Type of notification (booking_confirmation, appointment_reminder, etc.)
notification_type      # Channel type (email, sms, etc.)
template_name          # Email template to use
recipient             # User to receive the notification
subject               # Notification subject
message               # Notification content
scheduled_time         # When to send
status                # Delivery status
error_message          # Error details
```

## Integration Example

```python
# Creating an appointment with both reminders and notifications
appointment = Appointment.objects.create(...)

# Send immediate notifications
# Email notification for patient
AppointmentNotification.objects.create(
    appointment=appointment,
    recipient=appointment.patient,
    notification_type='email',
    event_type='booking_confirmation',
    subject='Appointment Confirmation',
    message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} has been scheduled.',
    scheduled_time=timezone.now()
)

# SMS notification for patient
AppointmentNotification.objects.create(
    appointment=appointment,
    recipient=appointment.patient,
    notification_type='sms',
    event_type='booking_confirmation',
    subject='Appointment Confirmation',
    message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} has been scheduled.',
    scheduled_time=timezone.now()
)

# Email notification for doctor
AppointmentNotification.objects.create(
    appointment=appointment,
    recipient=appointment.doctor.user,
    notification_type='email',
    event_type='booking_confirmation',
    subject='New Appointment',
    message=f'New appointment scheduled with {appointment.patient.get_full_name()}.',
    scheduled_time=timezone.now()
)

# Create reminders for later
appointment.create_reminders()
```

## Recommendation

1. Use **AppointmentReminder** for:
   - Managing scheduled reminders
   - Complex retry logic
   - Detailed tracking
   - Multiple reminders per appointment

2. Use **AppointmentNotification** for:
   - Immediate notifications (booking confirmations)
   - Status change notifications
   - Template-based emails
   - Multi-channel delivery (email, SMS)

3. Consider consolidating these systems if:
   - You don't need detailed reminder tracking
   - Your reminder system is simple
   - You want to reduce code complexity 