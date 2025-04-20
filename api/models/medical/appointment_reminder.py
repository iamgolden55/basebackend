from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class AppointmentReminder(models.Model):
    """
    Model to manage automated reminders for appointments
    """
    REMINDER_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('whatsapp', 'WhatsApp'),
    ]

    REMINDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    # Basic Information
    appointment = models.ForeignKey(
        'api.Appointment',
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    reminder_type = models.CharField(
        max_length=20,
        choices=REMINDER_TYPE_CHOICES
    )
    
    # Scheduling
    scheduled_time = models.DateTimeField()
    time_before_appointment = models.DurationField(
        help_text="Time before appointment to send reminder"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=REMINDER_STATUS_CHOICES,
        default='pending'
    )
    
    # Content
    subject = models.CharField(
        max_length=255,
        help_text="Subject line for email reminders"
    )
    message = models.TextField(
        help_text="Reminder message content"
    )
    
    # Recipient Information
    recipient_name = models.CharField(max_length=255)
    recipient_contact = models.CharField(
        max_length=255,
        help_text="Email address or phone number"
    )
    
    # Delivery Information
    sent_at = models.DateTimeField(
        null=True,
        blank=True
    )
    delivery_status = models.CharField(
        max_length=50,
        blank=True,
        help_text="Delivery status from provider"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if delivery failed"
    )
    
    # Tracking
    opened_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When recipient opened the reminder"
    )
    clicked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When recipient clicked any links"
    )
    
    # Retry Information
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_time']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_time']),
            models.Index(fields=['reminder_type']),
        ]

    def __str__(self):
        return f"{self.get_reminder_type_display()} reminder for {self.appointment}"

    def clean(self):
        """Validate reminder"""
        if self.scheduled_time >= self.appointment.appointment_date:
            raise ValidationError("Reminder must be scheduled before appointment time")
            
        if self.status == 'sent' and not self.sent_at:
            raise ValidationError("Sent reminder must have sent timestamp")
            
        if self.retry_count > self.max_retries:
            raise ValidationError("Retry count cannot exceed max retries")

    def save(self, *args, **kwargs):
        # Set recipient information from appointment if not provided
        if not self.recipient_name:
            self.recipient_name = self.appointment.patient.get_full_name()
            
        if not self.recipient_contact:
            if self.reminder_type == 'email':
                self.recipient_contact = self.appointment.patient.email
            elif self.reminder_type in ['sms', 'whatsapp']:
                self.recipient_contact = self.appointment.patient.phone_number
                
        # Calculate scheduled time if not set
        if not self.scheduled_time:
            self.scheduled_time = (
                self.appointment.appointment_date - self.time_before_appointment
            )
            
        self.clean()
        super().save(*args, **kwargs)

    def mark_as_sent(self, delivery_status=None):
        """Mark reminder as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        if delivery_status:
            self.delivery_status = delivery_status
        self.save()

    def mark_as_failed(self, error_message=None):
        """Mark reminder as failed"""
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
            
        # Schedule retry if possible
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            self.next_retry_at = self.calculate_next_retry_time()
            self.status = 'pending'
            
        self.save()

    def calculate_next_retry_time(self):
        """Calculate next retry time using exponential backoff"""
        from datetime import timedelta
        
        # Exponential backoff: 5min, 15min, 45min
        delay_minutes = 5 * (3 ** (self.retry_count - 1))
        return timezone.now() + timedelta(minutes=delay_minutes)

    def track_open(self):
        """Track when reminder was opened"""
        self.opened_at = timezone.now()
        self.save()

    def track_click(self):
        """Track when reminder links were clicked"""
        self.clicked_at = timezone.now()
        self.save()

    @property
    def is_due(self):
        """Check if reminder is due to be sent"""
        return (
            self.status == 'pending' and
            self.scheduled_time <= timezone.now() and
            (not self.next_retry_at or self.next_retry_at <= timezone.now())
        )

    @property
    def can_retry(self):
        """Check if reminder can be retried"""
        return (
            self.status == 'failed' and
            self.retry_count < self.max_retries
        )

    @property
    def is_delivered(self):
        """Check if reminder was successfully delivered"""
        return (
            self.status == 'sent' and
            self.delivery_status in ['delivered', 'opened', 'clicked']
        )

    def get_reminder_context(self):
        """Get context data for reminder template"""
        appointment = self.appointment
        return {
            'patient_name': self.recipient_name,
            'doctor_name': f"Dr. {appointment.doctor.user.get_full_name()}",
            'appointment_date': appointment.appointment_date,
            'appointment_type': appointment.get_appointment_type_display(),
            'hospital_name': appointment.hospital.name,
            'department_name': appointment.department.name,
            'cancellation_url': self.generate_cancellation_url(),
            'reschedule_url': self.generate_reschedule_url(),
        }

    def generate_cancellation_url(self):
        """Generate URL for cancelling appointment"""
        # Implementation depends on your URL structure
        return f"/appointments/{self.appointment.appointment_id}/cancel/"

    def generate_reschedule_url(self):
        """Generate URL for rescheduling appointment"""
        # Implementation depends on your URL structure
        return f"/appointments/{self.appointment.appointment_id}/reschedule/"

    @classmethod
    def create_appointment_reminders(cls, appointment):
        """Create standard set of reminders for an appointment"""
        from datetime import timedelta
        
        # Create email reminders
        if appointment.patient.email:
            cls.objects.create(
                appointment=appointment,
                reminder_type='email',
                time_before_appointment=timedelta(days=2),
                subject=f"Appointment Reminder: {appointment.get_appointment_type_display()}",
                message=f"Dear {appointment.patient.get_full_name()},\n\n"
                       f"This is a reminder for your upcoming appointment..."
            )
            
        # Create SMS reminders
        if appointment.patient.phone_number:
            cls.objects.create(
                appointment=appointment,
                reminder_type='sms',
                time_before_appointment=timedelta(days=1),
                message=f"Reminder: Your appointment with Dr. {appointment.doctor.user.get_full_name()} "
                       f"is tomorrow at {appointment.appointment_date.strftime('%I:%M %p')}"
            )
            
            # Day-of reminder
            cls.objects.create(
                appointment=appointment,
                reminder_type='sms',
                time_before_appointment=timedelta(hours=2),
                message=f"Your appointment with Dr. {appointment.doctor.user.get_full_name()} "
                       f"is in 2 hours at {appointment.hospital.name}"
            ) 