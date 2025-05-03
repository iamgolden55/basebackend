from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..base import TimestampedModel
from .appointment_notification import AppointmentNotification
from ..medical_staff.doctor import Doctor

class Appointment(TimestampedModel):
    """
    Model to manage medical appointments with enhanced validation and hospital registration checks
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
        ('referred', 'Referred'),
        ('rejected', 'Rejected')
    ]

    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency')
    ]

    APPOINTMENT_TYPE_CHOICES = [
        ('first_visit', 'First Visit'),
        ('follow_up', 'Follow Up'),
        ('consultation', 'Consultation'),
        ('procedure', 'Procedure'),
        ('test', 'Medical Test'),
        ('vaccination', 'Vaccination'),
        ('therapy', 'Therapy')
    ]

    # Basic Information
    appointment_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique identifier for the appointment"
    )
    patient = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='appointments'
    )
    hospital = models.ForeignKey(
        'api.Hospital',
        on_delete=models.PROTECT,
        related_name='appointments'
    )
    department = models.ForeignKey(
        'api.Department',
        on_delete=models.PROTECT,
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        'api.Doctor',
        on_delete=models.PROTECT,
        related_name='appointments'
    )

    # Appointment Details
    appointment_type = models.CharField(
        max_length=20,
        choices=APPOINTMENT_TYPE_CHOICES,
        default='consultation'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Scheduling
    appointment_date = models.DateTimeField()
    duration = models.PositiveIntegerField(
        default=30,
        help_text="Duration in minutes"
    )
    
    # Medical Information
    chief_complaint = models.TextField(
        blank=True,
        help_text="Primary reason for visit"
    )
    symptoms = models.TextField(
        blank=True,
        help_text="Description of symptoms"
    )
    medical_history = models.TextField(
        blank=True,
        help_text="Relevant medical history"
    )
    allergies = models.TextField(
        blank=True,
        help_text="Known allergies"
    )
    current_medications = models.TextField(
        blank=True,
        help_text="Current medications"
    )
    
    # Payment Information
    fee = models.ForeignKey(
        'api.AppointmentFee',
        on_delete=models.PROTECT,
        related_name='appointments',
        null=True,
        blank=True
    )
    is_insurance_based = models.BooleanField(default=False)
    insurance_details = models.JSONField(null=True, blank=True)
    payment_required = models.BooleanField(default=False)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Payment Pending'),
            ('partial', 'Partial Payment'),
            ('completed', 'Payment Completed'),
            ('waived', 'Payment Waived'),
            ('insurance', 'Insurance Processing'),
            ('refunded', 'Refunded')
        ],
        default='waived'
    )
    
    # Approval and Referral
    approved_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_appointments'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(null=True, blank=True)
    referred_to_hospital = models.ForeignKey(
        'api.Hospital',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='referred_appointments'
    )
    referral_reason = models.TextField(null=True, blank=True)
    referral_date = models.DateTimeField(null=True, blank=True)
    
    # Additional Information
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the appointment"
    )
    cancellation_reason = models.TextField(
        blank=True,
        help_text="Reason for cancellation if applicable"
    )
    
    # Reminders and Notifications
    reminder_sent = models.BooleanField(default=False)
    last_reminder_sent = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Status Timestamps
    cancelled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-appointment_date']
        indexes = [
            models.Index(fields=['appointment_date']),
            models.Index(fields=['status']),
            models.Index(fields=['appointment_id']),
        ]
        permissions = [
            ("can_approve_appointments", "Can approve appointments"),
            ("can_refer_appointments", "Can refer appointments"),
            ("can_view_all_appointments", "Can view all appointments"),
        ]

    def __str__(self):
        return f"{self.appointment_id} - {self.patient.get_full_name()} - {self.appointment_date}"

    def clean(self):
        """Validate appointment data"""
        super().clean()  # Call parent's clean first
        
        # Validate appointment date is not in the past
        if self.appointment_date:
            # Ensure timezone-aware dates and remove microseconds
            now = timezone.now().replace(microsecond=0)
            appointment_date = self.appointment_date.replace(microsecond=0)
            
            # Debug output for timezone information
            print(f"Model validation - Current time: {now} ({now.tzinfo})")
            print(f"Model validation - Appointment time: {appointment_date} ({appointment_date.tzinfo})")
            
            if appointment_date <= now:
                raise ValidationError({
                    'appointment_date': ["Appointment cannot be scheduled in the past or at the current time"]
                })
            
        # Validate hospital registration
        if not self._validate_hospital_registration():
            raise ValidationError({
                'hospital': ["Patient must be registered with the hospital"]
            })
            
        # For emergency appointments, bypass availability checks
        is_emergency = (
            self.priority == 'emergency' or 
            self.appointment_type == 'emergency'
        )
        
        # Check for existing appointments with the same specialty on the same day
        if not is_emergency:  # Skip for emergency appointments
            same_specialty_appointments = Appointment.objects.filter(
                patient=self.patient,
                appointment_date__date=self.appointment_date.date(),
                department=self.department,  # Same department/specialty
                status__in=['pending', 'confirmed', 'in_progress']
            )
            
            # Exclude current appointment if it's being updated
            if self.pk:
                same_specialty_appointments = same_specialty_appointments.exclude(pk=self.pk)
            
            if same_specialty_appointments.exists():
                raise ValidationError({
                    'appointment_date': ["You already have an appointment in this specialty on this date. Please choose another date or specialty."]
                })
            
        if not is_emergency:
            # Check if doctor is available
            if not self.doctor.is_available_at(self.appointment_date, is_emergency=False, current_appointment=self):
                raise ValidationError({
                    'appointment_date': ["Doctor is not available at this time"]
                })
                
            # Check if doctor can accept more appointments
            if not self.doctor.can_accept_appointment(self.appointment_date.date()):
                raise ValidationError({
                    'appointment_date': ["Doctor's schedule is full for this date"]
                })
            
        # Validate status transitions
        if self.pk:
            old_instance = Appointment.objects.get(pk=self.pk)
            if not self._is_valid_status_transition(old_instance.status, self.status):
                raise ValidationError({
                    'status': [f"Invalid status transition from {old_instance.status} to {self.status}"]
                })

    def _validate_hospital_registration(self):
        """Check if patient is registered with the hospital"""
        # Get patient's hospital registrations
        registrations = self.patient.get_registered_hospitals()
        
        # For emergency appointments, skip registration check
        if self.priority == 'emergency':
            return True
            
        # Check if patient is registered with this hospital
        return registrations.filter(hospital=self.hospital).exists()

    def save(self, *args, **kwargs):
        # Generate appointment ID if not provided
        if not self.appointment_id:
            self.appointment_id = self.generate_appointment_id()
            
        # Ensure validation is performed
        self.full_clean()
            
        # Update timestamps based on status
        if self.status == 'cancelled' and not self.cancelled_at:
            self.cancelled_at = timezone.now()
        elif self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            
        # Check if this is a new instance before saving
        _is_new = self.pk is None 
        
        super().save(*args, **kwargs)
        
        # Create booking confirmation notifications if it's a new appointment
        if _is_new:
            # Import here to avoid circular imports
            from api.utils.email import send_appointment_confirmation_email
            
            # Send email confirmation
            send_appointment_confirmation_email(self)
            
            # Create Email Notification
            AppointmentNotification.objects.create(
                appointment=self,
                notification_type='email',
                event_type='booking_confirmation',
                recipient=self.patient,
                subject=f"Appointment Booking Confirmation - {self.appointment_id}",
                message=(
                    f"Dear {self.patient.get_full_name()},\n\n"
                    f"Your appointment with Dr. {self.doctor.user.get_full_name()} "
                    f"at {self.hospital.name} ({self.department.name}) on "
                    f"{self.appointment_date.strftime('%Y-%m-%d %H:%M')} has been booked.\n\n"
                    f"Appointment ID: {self.appointment_id}\n"
                ),
                # Optionally specify a template name if using email templates
                # template_name='appointment_booking_confirmation' 
            )
            
            # Create SMS Notification (adjust message for SMS length constraints)
            AppointmentNotification.objects.create(
                appointment=self,
                notification_type='sms',
                event_type='booking_confirmation',
                recipient=self.patient,
                subject=f"Appt Confirmed: {self.appointment_id}", # Shorter subject for SMS?
                message=(
                    f"Appt Confirmed: Dr. {self.doctor.user.last_name}, "
                    f"{self.appointment_date.strftime('%b %d, %H:%M')}. "
                    f"ID: {self.appointment_id}. "
                    f"Hospital: {self.hospital.name[:10]}"
                )
                # template_name='sms_booking_confirmation' # Optional template
            )

    @staticmethod
    def generate_appointment_id():
        """Generate a unique appointment ID"""
        import uuid
        return f"APT-{uuid.uuid4().hex[:8].upper()}"

    def _is_valid_status_transition(self, old_status, new_status):
        """Check if status transition is valid"""
        valid_transitions = {
            'pending': ['confirmed', 'cancelled', 'rejected', 'referred'],
            'confirmed': ['in_progress', 'cancelled', 'no_show', 'referred'],
            'in_progress': ['completed', 'referred'],
            'completed': [],  # No further transitions allowed
            'cancelled': [],  # No further transitions allowed
            'no_show': [],    # No further transitions allowed
            'rejected': [],   # No further transitions allowed
            'referred': ['pending'],  # Can start new appointment process
            'rescheduled': ['pending']
        }
        return new_status in valid_transitions.get(old_status, [])

    def approve(self, approver, notes=None):
        """Approve the appointment"""
        if not approver.has_perm('api.can_approve_appointments'):
            raise ValidationError("User does not have permission to approve appointments")
            
        if self.status != 'pending':
            raise ValidationError("Only pending appointments can be approved")
            
        self.status = 'confirmed'
        self.approved_by = approver
        self.approval_date = timezone.now()
        if notes:
            self.approval_notes = notes
        self.save()
        
        # Import here to avoid circular imports
        from api.utils.email import send_appointment_confirmation_email
        
        # Send confirmation email when appointment is approved
        send_appointment_confirmation_email(self)
        
        # Create notification for approval
        from api.models.medical.appointment_notification import AppointmentNotification
        
        AppointmentNotification.objects.create(
            appointment=self,
            notification_type='email',
            event_type='appointment_approved',
            recipient=self.patient,
            subject=f"Appointment Approved - {self.appointment_id}",
            message=(
                f"Dear {self.patient.get_full_name()},\n\n"
                f"Your appointment with Dr. {self.doctor.user.get_full_name()} "
                f"at {self.hospital.name} ({self.department.name}) on "
                f"{self.appointment_date.strftime('%Y-%m-%d %H:%M')} has been approved.\n\n"
                f"Appointment ID: {self.appointment_id}\n"
            ),
            template_name='appointment_confirmation'
        )

    def refer(self, target_hospital, reason, referred_by):
        """Refer the appointment to another hospital"""
        if not referred_by.has_perm('api.can_refer_appointments'):
            raise ValidationError("User does not have permission to refer appointments")
            
        self.status = 'referred'
        self.referred_to_hospital = target_hospital
        self.referral_reason = reason
        self.referral_date = timezone.now()
        self.save()
        
        # Get target doctor from the same department at target hospital
        target_doctor = Doctor.objects.filter(
            hospital=target_hospital,
            department__name=self.department.name,
            is_active=True
        ).first()
        
        if not target_doctor:
            raise ValidationError("No active doctor found in the target department at the referred hospital")
        
        # Set appointment date to next available slot
        next_day = timezone.now() + timezone.timedelta(days=1)
        appointment_date = next_day.replace(
            hour=target_doctor.consultation_hours_start.hour,
            minute=target_doctor.consultation_hours_start.minute,
            second=0,
            microsecond=0
        )
        
        # Create new appointment at target hospital - don't require fee
        new_appointment = Appointment.objects.create(
            patient=self.patient,
            hospital=target_hospital,
            department=target_doctor.department,
            doctor=target_doctor,
            appointment_type=self.appointment_type,
            priority=self.priority,
            chief_complaint=self.chief_complaint,
            medical_history=self.medical_history,
            appointment_date=appointment_date,
            # fee=self.fee,  # Remove fee reference
            payment_required=False,
            payment_status='waived',
            status='pending'
        )
        
        # Send referral notifications
        AppointmentNotification.objects.create(
            appointment=self,
            notification_type='email',
            event_type='referral_notification',
            recipient=self.patient,
            subject=f"Appointment Referral - {self.appointment_id}",
            message=(
                f"Dear {self.patient.get_full_name()},\n\n"
                f"Your appointment has been referred to {target_hospital.name}.\n"
                f"Reason for referral: {reason}\n\n"
                f"New appointment details will be sent shortly."
            ),
            template_name='appointment_referral'
        )
        
        return new_appointment

    def cancel(self, reason=None):
        """Cancel the appointment"""
        if self.status not in ['pending', 'confirmed']:
            raise ValidationError("Only pending or confirmed appointments can be cancelled")
            
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save()  # This will trigger cancellation notification through save method

    def reschedule(self, new_date):
        """Reschedule the appointment"""
        if self.status not in ['pending', 'confirmed']:
            raise ValidationError("Only pending or confirmed appointments can be rescheduled")
            
        old_date = self.appointment_date
        self.appointment_date = new_date
        self.status = 'rescheduled'
        self.notes += f"\nRescheduled from {old_date} to {new_date}"
        self.save()
        
        # Send rescheduling notification
        AppointmentNotification.objects.create(
            appointment=self,
            notification_type='email',
            event_type='appointment_rescheduled',
            recipient=self.patient,
            subject=f"Appointment Rescheduled - {self.appointment_id}",
            message=(
                f"Dear {self.patient.get_full_name()},\n\n"
                f"Your appointment has been rescheduled:\n"
                f"From: {old_date}\n"
                f"To: {new_date}\n\n"
                f"If this time is not convenient, please contact us to arrange an alternative."
            ),
            template_name='appointment_rescheduled'
        )

    def create_reminders(self):
        """Create reminders for the appointment"""
        reminder_schedule = [
            {'days_before': 7, 'type': 'email'},  # 1 week before
            {'days_before': 2, 'type': 'email'},  # 2 days before
            {'days_before': 1, 'type': 'sms'},    # 1 day before
            {'hours_before': 2, 'type': 'sms'}    # 2 hours before
        ]
        
        AppointmentNotification.create_reminders(self, reminder_schedule)
        
        # Update fields directly in the database to avoid recursive save
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE api_appointment SET reminder_sent = %s, last_reminder_sent = %s WHERE id = %s",
                [True, timezone.now(), self.id]
            )

    @property
    def is_upcoming(self):
        """Check if appointment is upcoming"""
        return (
            self.status in ['pending', 'confirmed'] and
            self.appointment_date > timezone.now()
        )

    @property
    def can_be_cancelled(self):
        """Check if appointment can be cancelled"""
        return (
            self.status in ['pending', 'confirmed'] and
            self.appointment_date > timezone.now()
        )

    @property
    def needs_reminder(self):
        """Check if reminder needs to be sent"""
        if not self.is_upcoming:
            return False
            
        if not self.reminder_sent:
            return True
            
        if self.last_reminder_sent:
            # Check if last reminder was sent more than 24 hours ago
            return (timezone.now() - self.last_reminder_sent).days >= 1
            
        return True

    def get_appointment_summary(self):
        """Get summary of appointment details"""
        return {
            'appointment_id': self.appointment_id,
            'patient': self.patient.get_full_name(),
            'doctor': f"Dr. {self.doctor.user.get_full_name()}",
            'department': self.department.name,
            'hospital': self.hospital.name,
            'date': self.appointment_date,
            'status': self.status,
            'type': self.appointment_type,
            'priority': self.priority,
            'payment_status': self.payment_status,
            'is_insurance_based': self.is_insurance_based,
            'is_upcoming': self.is_upcoming,
            'can_be_cancelled': self.can_be_cancelled
        }

class AppointmentType(models.Model):
    id = models.CharField(max_length=50, primary_key=True)  # e.g., "first_visit"
    name = models.CharField(max_length=100)  # e.g., "First Visit"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    hospital = models.ForeignKey('Hospital', on_delete=models.CASCADE, null=True, blank=True)  # Optional - for hospital-specific types
    
    def __str__(self):
        return self.name 