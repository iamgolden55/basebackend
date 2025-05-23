from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from ..base import TimestampedModel

class AppointmentNotification(TimestampedModel):
    """
    Model to manage notifications for appointments including emails, SMS, and in-app notifications
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'In-App Notification'),
        ('whatsapp', 'WhatsApp')
    ]

    EVENT_TYPE_CHOICES = [
        ('booking_confirmation', 'Booking Confirmation'),
        ('appointment_reminder', 'Appointment Reminder'),
        ('appointment_update', 'Appointment Update'),
        ('appointment_cancellation', 'Appointment Cancellation'),
        ('appointment_rescheduled', 'Appointment Rescheduled'),
        ('payment_reminder', 'Payment Reminder'),
        ('payment_confirmation', 'Payment Confirmation'),
        ('doctor_unavailable', 'Doctor Unavailable'),
        ('referral_notification', 'Referral Notification'),
        ('follow_up_reminder', 'Follow-up Reminder'),
        ('emergency_notification', 'Emergency Notification'),
        ('test_results_available', 'Test Results Available'),
        ('pre_appointment_instructions', 'Pre-appointment Instructions')
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ]

    # Basic Information
    appointment = models.ForeignKey(
        'api.Appointment',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES
    )
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPE_CHOICES
    )
    recipient = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.CASCADE,
        related_name='appointment_notifications'
    )

    # Content
    subject = models.CharField(max_length=255)
    message = models.TextField()
    template_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Template to use for notification"
    )

    # Status and Tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    scheduled_time = models.DateTimeField()
    sent_time = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)

    # Tracking Information
    opened_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When recipient opened the notification"
    )
    clicked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When recipient clicked any links"
    )
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Next scheduled retry time"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_time']),
            models.Index(fields=['appointment', 'event_type']),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.recipient.email} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.scheduled_time:
            self.scheduled_time = timezone.now()
        super().save(*args, **kwargs)

    def calculate_next_retry_time(self):
        """Calculate next retry time using exponential backoff"""
        if self.retry_count >= self.max_retries:
            return None
            
        # Exponential backoff: 5min, 15min, 45min
        delay_minutes = 5 * (3 ** self.retry_count)
        return timezone.now() + timezone.timedelta(minutes=delay_minutes)

    def track_open(self):
        """Track when notification was opened"""
        self.opened_at = timezone.now()
        self.save(update_fields=['opened_at'])

    def track_click(self):
        """Track when notification links were clicked"""
        self.clicked_at = timezone.now()
        self.save(update_fields=['clicked_at'])

    @property
    def is_delivered(self):
        """Check if notification was successfully delivered"""
        return self.status == 'sent' and (self.opened_at or self.clicked_at)

    @classmethod
    def create_reminders(cls, appointment, reminder_schedule):
        """
        Create multiple reminders for an appointment
        
        reminder_schedule: List of dictionaries with timing and type
        Example:
        [
            {'days_before': 2, 'type': 'email'},
            {'days_before': 1, 'type': 'sms'},
            {'hours_before': 2, 'type': 'sms'}
        ]
        """
        for schedule in reminder_schedule:
            # Calculate scheduled time
            if 'days_before' in schedule:
                scheduled_time = appointment.appointment_date - timezone.timedelta(days=schedule['days_before'])
            elif 'hours_before' in schedule:
                scheduled_time = appointment.appointment_date - timezone.timedelta(hours=schedule['hours_before'])
            else:
                continue

            # Create notification
            notification = cls.objects.create(
                appointment=appointment,
                notification_type=schedule['type'],
                event_type='appointment_reminder',
                recipient=appointment.patient,
                subject=f"Appointment Reminder - {appointment.appointment_id}",
                template_name='appointment_reminder',
                scheduled_time=scheduled_time
            )

            # Set message for SMS/WhatsApp
            if schedule['type'] in ['sms', 'whatsapp']:
                notification.message = (
                    f"Reminder: Your appointment (ID: {appointment.appointment_id})\n"
                    f"with Dr. {appointment.doctor.user.get_full_name()}\n"
                    f"is on {appointment.appointment_date.strftime('%d/%m/%Y at %I:%M %p')}"
                )
                notification.save()

    def send(self):
        """Enhanced send method with retry logic"""
        try:
            if self.notification_type == 'email':
                self._send_email()
            elif self.notification_type == 'sms':
                self._send_sms()
            elif self.notification_type == 'whatsapp':
                self._send_whatsapp()
            elif self.notification_type == 'in_app':
                self._send_in_app()

            self.status = 'sent'
            self.sent_time = timezone.now()
            self.save()
            return True
        except Exception as e:
            self.status = 'failed'
            self.error_message = str(e)
            self.retry_count += 1
            
            # Schedule retry if possible
            if self.retry_count < self.max_retries:
                self.next_retry_at = self.calculate_next_retry_time()
                self.status = 'pending'
            
            self.save()
            return False

    @property
    def can_retry(self):
        """Check if notification can be retried"""
        return (
            self.status == 'failed' and
            self.retry_count < self.max_retries
        )

    @property
    def is_due(self):
        """Check if notification is due to be sent"""
        return (
            self.status == 'pending' and
            self.scheduled_time <= timezone.now() and
            (not self.next_retry_at or self.next_retry_at <= timezone.now())
        )

    def _send_email(self):
        """Send email notification"""
        context = self._get_template_context()
        
        if self.template_name:
            try:
                # Try with notifications/email path first
                html_message = render_to_string(
                    f'notifications/email/{self.template_name}.html',
                    context
                )
                text_message = render_to_string(
                    f'notifications/email/{self.template_name}.txt',
                    context
                )
            except:
                # If template not found, try with email path
                html_message = render_to_string(
                    f'email/{self.template_name}.html',
                    context
                )
                text_message = strip_tags(html_message)
        else:
            html_message = self.message
            text_message = self.message

        send_mail(
            subject=self.subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.recipient.email],
            html_message=html_message
        )

    def _send_sms(self):
        """Send SMS notification"""
        if not self.recipient.phone:
            raise ValueError("Recipient phone number not available")

        # Implement SMS sending logic here using your preferred provider
        # Example using Twilio:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=self.message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=self.recipient.phone
        )
        
        return message.sid

    def _send_whatsapp(self):
        """Send WhatsApp notification"""
        if not self.recipient.phone:
            raise ValueError("Recipient phone number not available")

        # Implement WhatsApp sending logic here
        # Example using Twilio WhatsApp:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=self.message,
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{self.recipient.phone}"
        )
        
        return message.sid

    def _send_in_app(self):
        """Create in-app notification"""
        from api.models.notifications import InAppNotification
        
        InAppNotification.objects.create(
            user=self.recipient,
            title=self.subject,
            message=self.message,
            notification_type='appointment',
            reference_id=self.appointment.appointment_id
        )

    def _get_template_context(self):
        """Get context data for templates"""
        context = {
            'patient_name': self.recipient.get_full_name(),
            'appointment_id': self.appointment.appointment_id,
            'doctor_name': f"Dr. {self.appointment.doctor.user.get_full_name()}" if self.appointment.doctor else "TBD",
            'hospital_name': self.appointment.hospital.name,
            'department_name': self.appointment.department.name,
            'appointment_date': self.appointment.appointment_date,
            'appointment_date_formatted': self.appointment.appointment_date.strftime('%B %d, %Y at %I:%M %p'),
            'appointment_date_only': self.appointment.appointment_date.strftime('%d %B, %Y'),
            'appointment_time_only': self.appointment.appointment_date.strftime('%I:%M %p'),
            'frontend_url': settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else '',
            'subject': self.subject,
            'message': self.message,
        }
        
        # Status-specific context
        status_dict = dict(self.appointment._meta.get_field('status').choices)
        context['status'] = self.appointment.status
        context['status_display'] = status_dict.get(self.appointment.status, self.appointment.status)
        
        return context

    @classmethod
    def create_booking_confirmation(cls, appointment):
        """Create booking confirmation notification"""
        subject = f"Appointment Confirmation - {appointment.appointment_id}"
        
        # Create email notification
        cls.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='booking_confirmation',
            recipient=appointment.patient,
            subject=subject,
            template_name='appointment_booking_confirmation'
        )

        # Create SMS notification if phone number available
        if appointment.patient.phone:
            sms_message = (
                f"Appointment confirmed: {appointment.appointment_id}\n"
                f"Date: {appointment.appointment_date}\n"
                f"Doctor: Dr. {appointment.doctor.user.get_full_name()}\n"
                f"Hospital: {appointment.hospital.name}"
            )
            cls.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='booking_confirmation',
                recipient=appointment.patient,
                subject=subject,
                message=sms_message
            )

    @classmethod
    def create_appointment_reminder(cls, appointment, days_before=1):
        """Create appointment reminder notification"""
        subject = f"Appointment Reminder - {appointment.appointment_id}"
        reminder_time = appointment.appointment_date - timezone.timedelta(days=days_before)

        # Create email reminder
        cls.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='appointment_reminder',
            recipient=appointment.patient,
            subject=subject,
            template_name='appointment_reminder',
            scheduled_time=reminder_time
        )

        # Create SMS reminder if phone number available
        if appointment.patient.phone:
            sms_message = (
                f"Reminder: Your appointment (ID: {appointment.appointment_id})\n"
                f"is tomorrow at {appointment.appointment_date.strftime('%I:%M %p')}\n"
                f"with Dr. {appointment.doctor.user.get_full_name()}"
            )
            cls.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='appointment_reminder',
                recipient=appointment.patient,
                subject=subject,
                message=sms_message,
                scheduled_time=reminder_time
            )

    @classmethod
    def create_cancellation_notification(cls, appointment, reason=None):
        """Create cancellation notification"""
        subject = f"Appointment Cancelled - {appointment.appointment_id}"

        # Create email notification
        cls.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='appointment_cancellation',
            recipient=appointment.patient,
            subject=subject,
            template_name='appointment_cancellation'
        )

        # Create SMS notification if phone number available
        if appointment.patient.phone:
            sms_message = (
                f"Your appointment (ID: {appointment.appointment_id})\n"
                f"scheduled for {appointment.appointment_date.strftime('%d/%m/%Y %I:%M %p')}\n"
                f"has been cancelled."
            )
            cls.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='appointment_cancellation',
                recipient=appointment.patient,
                subject=subject,
                message=sms_message
            )

    @classmethod
    def create_payment_reminder(cls, appointment):
        """Create payment reminder notification"""
        subject = f"Payment Reminder - Appointment {appointment.appointment_id}"
        message = (
            f"Dear {appointment.patient.get_full_name()},\n\n"
            f"This is a reminder to complete the payment for your appointment:\n"
            f"- Appointment ID: {appointment.appointment_id}\n"
            f"- Amount Due: {appointment.fee.base_fee}\n"
            f"- Due Date: {appointment.appointment_date.strftime('%d/%m/%Y')}\n\n"
            f"Please complete the payment to confirm your appointment."
        )

        # Create email notification
        cls.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='payment_reminder',
            recipient=appointment.patient,
            subject=subject,
            message=message,
            template_name='payment_reminder'
        )

        # Create SMS notification if phone number available
        if appointment.patient.phone:
            sms_message = (
                f"Payment Reminder: Please complete payment of "
                f"{appointment.fee.base_fee} for appointment "
                f"{appointment.appointment_id}"
            )
            cls.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='payment_reminder',
                recipient=appointment.patient,
                subject=subject,
                message=sms_message
            )

    @classmethod
    def create_rescheduling_notification(cls, appointment):
        """Create notification for rescheduled appointment"""
        subject = f"Appointment Rescheduled - {appointment.appointment_id}"

        # Create email notification
        cls.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='appointment_rescheduled',
            recipient=appointment.patient,
            subject=subject,
            template_name='appointment_rescheduled'
        )

        # Create SMS notification if phone number available
        if appointment.patient.phone:
            sms_message = (
                f"Your appointment (ID: {appointment.appointment_id})\n"
                f"has been rescheduled to {appointment.appointment_date.strftime('%d/%m/%Y %I:%M %p')}\n"
                f"with Dr. {appointment.doctor.user.get_full_name()}"
            )
            cls.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='appointment_rescheduled',
                recipient=appointment.patient,
                subject=subject,
                message=sms_message
            )

    @classmethod
    def create_payment_confirmation(cls, appointment):
        """Create payment confirmation notification"""
        subject = f"Payment Confirmation - {appointment.appointment_id}"

        # Create email notification
        cls.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='payment_confirmation',
            recipient=appointment.patient,
            subject=subject,
            template_name='payment_confirmation'
        )

        # Create SMS notification if phone number available
        if appointment.patient.phone:
            sms_message = (
                f"Payment received for appointment {appointment.appointment_id}.\n"
                f"Your appointment on {appointment.appointment_date.strftime('%d/%m/%Y %I:%M %p')}\n"
                f"is now fully confirmed."
            )
            cls.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='payment_confirmation',
                recipient=appointment.patient,
                subject=subject,
                message=sms_message
            )

    @classmethod
    def create_doctor_unavailable_notification(cls, appointment):
        """Create notification for doctor unavailability"""
        subject = f"Doctor Unavailable - {appointment.appointment_id}"

        # Create email notification
        cls.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='doctor_unavailable',
            recipient=appointment.patient,
            subject=subject,
            template_name='doctor_unavailable'
        )

        # Create SMS notification if phone number available
        if appointment.patient.phone:
            sms_message = (
                f"Important: Dr. {appointment.doctor.user.get_full_name()} is unavailable for your\n"
                f"appointment on {appointment.appointment_date.strftime('%d/%m/%Y %I:%M %p')}.\n"
                f"Please contact us to reschedule or choose another doctor."
            )
            cls.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='doctor_unavailable',
                recipient=appointment.patient,
                subject=subject,
                message=sms_message
            )

    @classmethod
    def create_referral_notification(cls, appointment, referred_department):
        """Create notification for medical referral"""
        subject = f"Medical Referral - {appointment.appointment_id}"

        # Create email notification
        cls.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='referral_notification',
            recipient=appointment.patient,
            subject=subject,
            template_name='referral_notification'
        )

        # Create SMS notification if phone number available
        if appointment.patient.phone:
            sms_message = (
                f"Medical Referral: Dr. {appointment.doctor.user.get_full_name()}\n"
                f"has referred you to the {referred_department} department.\n"
                f"Please schedule your specialist appointment."
            )
            cls.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='referral_notification',
                recipient=appointment.patient,
                subject=subject,
                message=sms_message
            )

    @classmethod
    def create_follow_up_reminder(cls, appointment, recommended_date=None):
        """Create follow-up appointment reminder notification"""
        subject = f"Follow-up Appointment Reminder - {appointment.appointment_id}"

        # Create email notification
        cls.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='follow_up_reminder',
            recipient=appointment.patient,
            subject=subject,
            template_name='follow_up_reminder'
        )

        # Create SMS notification if phone number available
        if appointment.patient.phone:
            sms_message = (
                f"Follow-up Reminder: Please schedule your follow-up appointment\n"
                f"with Dr. {appointment.doctor.user.get_full_name()}"
            )
            if recommended_date:
                sms_message += f"\nRecommended by: {recommended_date.strftime('%d/%m/%Y')}"
            
            cls.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='follow_up_reminder',
                recipient=appointment.patient,
                subject=subject,
                message=sms_message
            )

    @classmethod
    def create_emergency_notification(cls, appointment, emergency_contact, message=None):
        """Create emergency notification"""
        subject = f"URGENT: Important Medical Information - {appointment.appointment_id}"

        # Create email notification with high priority
        notification = cls.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='emergency_notification',
            recipient=appointment.patient,
            subject=subject,
            template_name='emergency_notification'
        )
        notification.scheduled_time = timezone.now()  # Send immediately
        notification.save()

        # Create SMS notification if phone number available
        if appointment.patient.phone:
            sms_message = (
                f"URGENT MEDICAL NOTIFICATION\n"
                f"Please contact {emergency_contact} immediately regarding "
                f"appointment {appointment.appointment_id}."
            )
            if message:
                sms_message += f"\nRe: {message}"
            
            urgent_sms = cls.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='emergency_notification',
                recipient=appointment.patient,
                subject=subject,
                message=sms_message
            )
            urgent_sms.scheduled_time = timezone.now()  # Send immediately
            urgent_sms.save()

    @classmethod
    def create_test_results_notification(cls, appointment):
        """Create notification for test results availability"""
        subject = f"Test Results Available - {appointment.appointment_id}"

        # Create email notification
        cls.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='test_results_available',
            recipient=appointment.patient,
            subject=subject,
            template_name='test_results_available'
        )

        # Create SMS notification if phone number available
        if appointment.patient.phone:
            sms_message = (
                f"Your test results from appointment {appointment.appointment_id} "
                f"are now available. Please log in to your patient portal to view them."
            )
            cls.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='test_results_available',
                recipient=appointment.patient,
                subject=subject,
                message=sms_message
            )

    @classmethod
    def create_pre_appointment_instructions(cls, appointment, days_before=2):
        """Create pre-appointment instructions notification"""
        subject = f"Pre-appointment Instructions - {appointment.appointment_id}"
        instruction_time = appointment.appointment_date - timezone.timedelta(days=days_before)

        # Create email notification
        cls.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='pre_appointment_instructions',
            recipient=appointment.patient,
            subject=subject,
            template_name='pre_appointment_instructions',
            scheduled_time=instruction_time
        )

        # Create SMS notification if phone number available
        if appointment.patient.phone:
            sms_message = (
                f"Important instructions for your appointment on "
                f"{appointment.appointment_date.strftime('%d/%m/%Y')}:\n"
                f"Please check your email for detailed preparation instructions."
            )
            cls.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='pre_appointment_instructions',
                recipient=appointment.patient,
                subject=subject,
                message=sms_message,
                scheduled_time=instruction_time
            )
            
    @classmethod
    def create_status_update_notification(cls, appointment):
        """Create notification for appointment status updates"""
        subject = f"Appointment Status Update - {appointment.appointment_id}"
        
        # Get status display name
        status_display = dict(appointment._meta.get_field('status').choices).get(appointment.status, appointment.status)
        
        # Create email notification
        email_notification = cls.objects.create(
            appointment=appointment,
            notification_type='email',
            event_type='appointment_update',
            recipient=appointment.patient,
            subject=subject,
            template_name='appointment_status_update',
            scheduled_time=timezone.now()
        )
        
        # Create SMS notification if phone number available
        if appointment.patient.phone:
            sms_message = (
                f"Your appointment (ID: {appointment.appointment_id}) "
                f"status has been updated to: {status_display}. "
                f"Date: {appointment.appointment_date.strftime('%d/%m/%Y %I:%M %p')}. "
                f"Please check your email for details."
            )
            sms_notification = cls.objects.create(
                appointment=appointment,
                notification_type='sms',
                event_type='appointment_update',
                recipient=appointment.patient,
                subject=subject,
                message=sms_message,
                scheduled_time=timezone.now()
            )
            
        return email_notification 