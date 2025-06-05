from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..base import TimestampedModel
from .appointment_notification import AppointmentNotification
from ..medical_staff.doctor import Doctor
import logging
logger = logging.getLogger(__name__)

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
        related_name='appointments',
        null=True,
        blank=True
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
    symptoms_data = models.JSONField(
        default=list,
        help_text="Structured symptoms data"
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
    referred_to_department = models.ForeignKey(
    'Department',
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name='referred_appointments'
)
    referral_reason = models.TextField(null=True, blank=True)
    referral_date = models.DateTimeField(null=True, blank=True)
    referred_from = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='referred_to'
    )
    
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
            
        # Only check doctor availability if a doctor is assigned and it's not an emergency
        if self.doctor and not is_emergency:
            if not self.doctor.is_available_at(self.appointment_date, is_emergency=False, current_appointment=self):
                raise ValidationError({
                    'appointment_date': ["Doctor is not available at this time"]
                })
                
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
            
        # Get the old status if this is an existing appointment
        old_status = None
        bypass_validation = kwargs.pop('bypass_validation', False)
        
        if self.pk:
            # This is an update, not a creation - get the old status
            old_instance = Appointment.objects.filter(pk=self.pk).first()
            if old_instance:
                old_status = old_instance.status
        
        # Check for valid status transition
        if old_status and self.status != old_status and not bypass_validation:
            if not self._is_valid_status_transition(old_status, self.status):
                raise ValidationError({
                    'status': [f'Invalid status transition from {old_status} to {self.status}']
                })
        
        # Update timestamp for status changes
        if old_status and self.status != old_status:
            if self.status == 'cancelled':
                self.cancelled_at = timezone.now()
            elif self.status == 'completed':
                self.completed_at = timezone.now()
        
        # Full validation (skip if bypassing)
        if not bypass_validation:
            self.full_clean()
        
        super().save(*args, **kwargs)
        
        # Handle notifications based on appointment status
        if self.pk is None:
            # New appointment - send booking confirmation
            from api.utils.email import send_appointment_confirmation_email
            send_appointment_confirmation_email(self)
            
            # Create notifications for new booking
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
                    f"Status: Pending doctor's confirmation\n"
                ),
                template_name='appointment_booking_confirmation'
            )
            
            if self.patient.phone:
                AppointmentNotification.objects.create(
                    appointment=self,
                    notification_type='sms',
                    event_type='booking_confirmation',
                    recipient=self.patient,
                    subject=f"Appt Booked: {self.appointment_id}",
                    message=(
                        f"Appt Booked: Dr. {self.doctor.user.last_name}, "
                        f"{self.appointment_date.strftime('%b %d, %H:%M')}. "
                        f"ID: {self.appointment_id}. "
                        f"Status: Pending"
                    )
                )
        
        elif old_status and self.status != old_status:
            # Status has changed - send status update notification
            from api.utils.email import send_appointment_status_update_email
            send_appointment_status_update_email(self)
            
            # Create status update notification
            AppointmentNotification.create_status_update_notification(self)
            
            # Special handling for confirmed appointments
            if self.status == 'confirmed':
                from api.utils.email import send_appointment_confirmation_email
                send_appointment_confirmation_email(self)
                self.create_reminders()  # Create reminder notifications

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
            'in_progress': ['completed', 'cancelled', 'referred'],
            'completed': [],
            'cancelled': [],
            'no_show': [],
            'rejected': [],
            'referred': [],
            'rescheduled': ['confirmed', 'cancelled']
        }
        return new_status in valid_transitions.get(old_status, [])

    def approve(self, doctor, notes=None):
        """Doctor accepts the appointment"""
        if self.status != 'pending':
            raise ValidationError("Only pending appointments can be accepted")
            
        # Check if doctor is a User with doctor_profile or a Doctor instance
        if hasattr(doctor, 'doctor_profile'):
            # doctor is a User with a doctor_profile
            self.approved_by = doctor
            doctor = doctor.doctor_profile
        else:
            # doctor is already a Doctor instance
            self.approved_by = doctor.user
        
        self.status = 'confirmed'
        self.doctor = doctor
        self.approval_date = timezone.now()
        
        # Handle optional notes for backward compatibility
        if notes:
            self.approval_notes = notes
        
        self.save()
        
        # Create notification for approval
        AppointmentNotification.objects.create(
            appointment=self,
            notification_type='email',
            event_type='appointment_accepted',
            recipient=self.patient,
            subject=f"Appointment Accepted - {self.appointment_id}",
            message=(
                f"Dear {self.patient.get_full_name()},\n\n"
                f"Your appointment has been accepted by Dr. {doctor.user.get_full_name()} "
                f"at {self.hospital.name} ({self.department.name}) on "
                f"{self.appointment_date.strftime('%Y-%m-%d %H:%M')}.\n\n"
                f"Appointment ID: {self.appointment_id}\n"
            ),
            template_name='appointment_confirmation'
        )

    def start_consultation(self, doctor):
        """Start the consultation - move to in_progress"""
        if self.status != 'confirmed':
            raise ValidationError("Only confirmed appointments can be started")
            
        if self.doctor != doctor:
            raise ValidationError("Only the assigned doctor can start the consultation")
            
        self.status = 'in_progress'
        self.save()

    def complete_consultation(self, doctor):
        """Complete the consultation"""
        if self.status != 'in_progress':
            raise ValidationError("Only in-progress appointments can be completed")
            
        if self.doctor != doctor:
            raise ValidationError("Only the assigned doctor can complete the consultation")
            
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def cancel(self, cancelled_by, reason=None):
        """Cancel the appointment with differentiation between patient and doctor cancellation"""
        if self.status not in ['pending', 'confirmed']:
            raise ValidationError("Only pending or confirmed appointments can be cancelled")
            
        is_doctor = hasattr(cancelled_by, 'doctor_profile')
        
        if is_doctor:
            # Doctor cancellation - return to pending state
            self.status = 'pending'
            self.doctor = None  # Remove doctor assignment
            self.notes += f"\nCancelled by Dr. {cancelled_by.get_full_name()}. Reason: {reason}"
        else:
            # Patient cancellation
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.cancellation_reason = reason
            
        self.save()
        
        # Send appropriate notification
        event_type = 'doctor_cancelled' if is_doctor else 'patient_cancelled'
        message = (
            f"Dear {self.patient.get_full_name()},\n\n"
            f"Your appointment ({self.appointment_id}) has been "
            f"{'returned to pending status' if is_doctor else 'cancelled'}.\n"
        )
        if reason:
            message += f"Reason: {reason}\n"
            
        if is_doctor:
            message += "\nAnother doctor from the department will be assigned to your appointment."
            
        AppointmentNotification.objects.create(
            appointment=self,
            notification_type='email',
            event_type=event_type,
            recipient=self.patient,
            subject=f"Appointment {'Status Update' if is_doctor else 'Cancellation'} - {self.appointment_id}",
            message=message,
            template_name='appointment_status_update'
        )

    def refer(self, target_hospital=None, target_department=None, reason=None, referred_by=None):
        print(f"\n=== REFERRAL DEBUG ===")
        print(f"Original Appointment ID: {self.id}")
        print(f"Requested By User: {referred_by} (Staff: {referred_by.is_staff}, Doctor: {hasattr(referred_by, 'doctor_profile')})")
        print(f"Target Hospital: {target_hospital.id if target_hospital else 'Same Hospital'}")
        print(f"Target Department: {target_department.id if target_department else 'Not Specified'}")
        print(f"Current Status: {self.status}")
        
        is_doctor = hasattr(referred_by, 'doctor_profile')
        if not (referred_by.has_perm('api.can_refer_appointments') or 
                referred_by.is_staff or 
                is_doctor):
            raise ValidationError("User does not have permission to refer appointments")

        if not target_hospital and not target_department:
            raise ValidationError("Either target_hospital or target_department must be specified")

        logger.debug(
            f"Referral processing - Original: {self.id}, "
            f"Target Hospital: {target_hospital.id if target_hospital else 'Same'}, "
            f"Target Dept: {target_department.id if target_department else 'Same'}, User Permissions: "
            f"{referred_by.has_perm('api.can_refer_appointments')}"
        )

        # Only update status if not already referred
        if self.status != 'referred':
            self.status = 'referred'
            self.referral_reason = reason
            self.referral_date = timezone.now()
        else:
            print("Appointment already referred - Skipping status update")
        
        if target_hospital:
            self.referred_to_hospital = target_hospital
        if target_department:
            self.referred_to_department = target_department
        
        self.save()

        # For inter-hospital referrals (existing behavior)
        if target_hospital:
            target_doctor = Doctor.objects.filter(
                hospital=target_hospital,
                department__name=self.department.name,
                is_active=True
            ).first()
            
            if not target_doctor:
                raise ValidationError("No active doctor found in the target department at the referred hospital")
            
            next_day = timezone.now() + timezone.timedelta(days=1)
            appointment_date = next_day.replace(
                hour=target_doctor.consultation_hours_start.hour,
                minute=target_doctor.consultation_hours_start.minute,
                second=0,
                microsecond=0
            )
            
            department = target_doctor.department
        else:  # Intra-hospital department referral
            department = target_department
            appointment_date = timezone.now() + timezone.timedelta(days=1)  # Default next day
        
        # Create new appointment
        new_appointment = Appointment.objects.create(
            patient=self.patient,
            hospital=target_hospital if target_hospital else self.hospital,
            department=target_department,  # Using target department
            doctor=None,
            appointment_type=self.appointment_type,
            priority=self.priority,
            chief_complaint=self.chief_complaint,
            symptoms=self.symptoms,
            symptoms_data=self.symptoms_data or [],
            medical_history=self.medical_history,
            allergies=self.allergies,
            current_medications=self.current_medications,
            appointment_date=appointment_date,
            duration=self.duration,
            status='pending',
            referred_from=self
        )
        
        print(f"\n=== NEW APPOINTMENT CREATED ===")
        print(f"New Appointment ID: {new_appointment.id}")
        print(f"Patient: {new_appointment.patient} (ID: {new_appointment.patient_id})")
        print(f"Scheduled Date: {new_appointment.appointment_date}")
        print(f"Status: {new_appointment.status}")
        print(f"Referred From: {self.id}\n")

        logger.debug(
            f"New referral appointment created - ID: {new_appointment.id}, "
            f"Patient: {new_appointment.patient_id}, "
            f"Date: {new_appointment.appointment_date}"
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
                f"Your appointment has been referred to {target_hospital.name if target_hospital else target_department.name} department.\n"
                f"Reason for referral: {reason}\n\n"
                f"New appointment details will be sent shortly."
            ),
            template_name='appointment_referral'
        )
        
        return new_appointment

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
            'doctor': f"Dr. {self.doctor.user.get_full_name()}" if self.doctor else "No Doctor Assigned",
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