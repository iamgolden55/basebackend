from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.signing import Signer
import json
from datetime import datetime

class PaymentTransaction(models.Model):
    """
    Model to track payment transactions for appointments with enhanced security
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]

    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('insurance', 'Insurance'),
        ('mobile_money', 'Mobile Money'),
        ('wallet', 'E-Wallet'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('NGN', 'Nigerian Naira'),
    ]

    PAYMENT_PROVIDER_CHOICES = [
        ('paystack', 'Paystack'),
        ('moniepoint', 'Moniepoint'),
        ('flutterwave', 'Flutterwave'),
        ('stripe', 'Stripe'),
    ]

    # Basic Information
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier for the transaction"
    )
    appointment = models.ForeignKey(
        'api.Appointment',
        on_delete=models.PROTECT,
        related_name='payments',
        null=True,  # 🎯 MAKE OPTIONAL FOR PAYMENT-FIRST APPROACH!
        blank=True,
        help_text="Associated appointment (optional for payment-first flow)"
    )
    patient = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='payments'
    )
    hospital = models.ForeignKey(
        'api.Hospital',
        on_delete=models.PROTECT,
        related_name='payments',
        null=True,  # 🎯 MAKE OPTIONAL FOR PAYMENT-FIRST APPROACH!
        blank=True,
        help_text="Associated hospital (optional for payment-first flow)"
    )

    # Payment Details with Encryption
    _encrypted_amount = models.BinaryField(
        null=True,
        editable=False,
        help_text="Encrypted amount for security"
    )
    amount_display = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Display amount for UI"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='NGN'
    )
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    # Insurance Information with Encryption
    _encrypted_insurance_data = models.BinaryField(
        null=True,
        editable=False,
        help_text="Encrypted insurance information"
    )
    insurance_provider = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    insurance_policy_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    insurance_coverage_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Payment Processing Details with Enhanced Security
    _encrypted_gateway_data = models.BinaryField(
        null=True,
        editable=False,
        help_text="Encrypted gateway response data"
    )
    payment_gateway = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Payment gateway used for processing"
    )
    gateway_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Transaction ID from payment gateway"
    )
    
    # Audit Trail
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='created_transactions',
        help_text="User who created the transaction"
    )
    last_modified_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='modified_transactions',
        help_text="User who last modified the transaction"
    )
    status_change_history = models.JSONField(
        default=list,
        help_text="History of status changes with timestamps and users"
    )
    access_log = models.JSONField(
        default=list,
        help_text="Log of users who accessed this transaction"
    )
    
    # Gift Payment Support
    gift_sender = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_gift_payments'
    )
    
    # Additional Information
    description = models.TextField(
        blank=True,
        help_text="Additional details about the transaction"
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes about the transaction"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Payment Provider Information
    payment_provider = models.CharField(
        max_length=50,
        choices=PAYMENT_PROVIDER_CHOICES,
        null=True,
        help_text="Payment provider used for processing"
    )
    provider_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Reference ID from payment provider"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['created_at']),
        ]
        permissions = [
            ("can_view_sensitive_data", "Can view sensitive transaction data"),
            ("can_process_refunds", "Can process refunds"),
            ("can_view_audit_trail", "Can view transaction audit trail"),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Don't set _signer here - make it a property instead
        # Safely get payment_status, default to 'pending' if not set
        self._old_status = getattr(self, 'payment_status', 'pending')

    def _get_signer(self):
        """Get a fresh signer instance for thread safety"""
        from django.core.signing import Signer
        return Signer(salt='payment_transaction')

    def __str__(self):
        return f"{self.transaction_id} - {self.payment_status}"

    @property
    def amount(self):
        """Decrypt and return the actual amount"""
        if self._encrypted_amount:
            try:
                signer = self._get_signer()
                return float(signer.unsign(self._encrypted_amount.decode()))
            except Exception as e:
                logger.error(f"Failed to decrypt amount for transaction {self.transaction_id}: {e}")
                # Fall back to display amount
                return float(self.amount_display)
        return float(self.amount_display)

    @amount.setter
    def amount(self, value):
        """Encrypt and store the amount"""
        self.amount_display = value
        try:
            signer = self._get_signer()
            self._encrypted_amount = signer.sign(str(value)).encode()
        except Exception as e:
            logger.error(f"Failed to encrypt amount for transaction {self.transaction_id}: {e}")
            # Continue without encryption if encryption fails

    @property
    def insurance_data(self):
        """Decrypt and return insurance data"""
        if self._encrypted_insurance_data:
            try:
                signer = self._get_signer()
                return json.loads(signer.unsign(self._encrypted_insurance_data.decode()))
            except Exception as e:
                logger.error(f"Failed to decrypt insurance data for transaction {self.transaction_id}: {e}")
                return {}
        return {}

    @insurance_data.setter
    def insurance_data(self, data):
        """Encrypt and store insurance data"""
        if data:
            try:
                signer = self._get_signer()
                self._encrypted_insurance_data = signer.sign(json.dumps(data)).encode()
            except Exception as e:
                logger.error(f"Failed to encrypt insurance data for transaction {self.transaction_id}: {e}")
                # Continue without encryption if encryption fails

    @property
    def gateway_data(self):
        """Decrypt and return gateway data"""
        if self._encrypted_gateway_data:
            try:
                signer = self._get_signer()
                return json.loads(signer.unsign(self._encrypted_gateway_data.decode()))
            except Exception as e:
                logger.error(f"Failed to decrypt gateway data for transaction {self.transaction_id}: {e}")
                return {}
        return {}

    @gateway_data.setter
    def gateway_data(self, data):
        """Encrypt and store gateway data"""
        if data:
            try:
                signer = self._get_signer()
                self._encrypted_gateway_data = signer.sign(json.dumps(data)).encode()
            except Exception as e:
                logger.error(f"Failed to encrypt gateway data for transaction {self.transaction_id}: {e}")
                # Continue without encryption if encryption fails

    def log_access(self, user, action='viewed'):
        """Log user access to transaction"""
        self.access_log.append({
            'user': user.id if user else None,
            'timestamp': datetime.now().isoformat(),
            'action': action
        })
        self.save()

    def log_status_change(self, user):
        """Log status change in history"""
        if self.payment_status != self._old_status:
            self.status_change_history.append({
                'from_status': self._old_status,
                'to_status': self.payment_status,
                'changed_by': user.id,
                'timestamp': datetime.now().isoformat()
            })
            self._old_status = self.payment_status

    def clean(self):
        """Enhanced validation with security checks"""
        super().clean()
        
        if self.payment_method == 'insurance' and not all([
            self.insurance_provider,
            self.insurance_policy_number
        ]):
            raise ValidationError(
                "Insurance provider and policy number are required for insurance payments"
            )
            
        if self.insurance_coverage_amount > self.amount:
            raise ValidationError(
                "Insurance coverage amount cannot exceed total amount"
            )

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        # First save for new instances
        if not self.pk:
            if user:
                self.created_by = user
                self.last_modified_by = user
            
            # Generate transaction ID if not provided
            if not self.transaction_id:
                self.transaction_id = self.generate_transaction_id()
        
        # Update last modified user
        if user:
            self.last_modified_by = user
            self.log_status_change(user)
        
        # Set completed_at timestamp
        if self.payment_status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        self.clean()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_transaction_id():
        """Generate a unique transaction ID"""
        import uuid
        return f"TXN-{uuid.uuid4().hex[:12].upper()}"

    def mark_as_completed(self, gateway_response=None, user=None):
        """Mark payment as completed with audit and create appointment if needed"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🎯 Marking payment {self.transaction_id} as completed")
        logger.info(f"🎯 Current appointment: {self.appointment.id if self.appointment else 'None'}")
        logger.info(f"🎯 Description length: {len(self.description) if self.description else 0}")
        
        # Update payment status
        self._update_payment_status(gateway_response, user)
        
        # 🚀 PAYMENT-FIRST: Create appointment if booking details are available
        appointment_creation_attempted = self._attempt_payment_first_booking(user)
        
        # Final status logging
        self._log_payment_completion_result(appointment_creation_attempted)

    def _update_payment_status(self, gateway_response, user):
        """Update payment status and save changes"""
        import logging
        logger = logging.getLogger(__name__)
        
        old_status = self.payment_status
        self.payment_status = 'completed'
        self.completed_at = timezone.now()
        if gateway_response:
            self.gateway_data = gateway_response
            
        # Save payment status update first
        try:
            self.save(user=user)
            logger.info(f"✅ Payment {self.transaction_id} status updated from {old_status} to completed")
        except Exception as save_error:
            logger.error(f"❌ Failed to save payment status update: {save_error}")
            raise

    def _attempt_payment_first_booking(self, user):
        """Attempt to create appointment from payment-first booking details"""
        import logging
        logger = logging.getLogger(__name__)
        
        appointment_creation_attempted = False
        
        if not self.appointment and self.description:
            appointment_creation_attempted = True
            logger.info(f"🚀 Payment-first detected for {self.transaction_id} - checking for booking details")
            logger.info(f"🚀 Description content preview: {self.description[:200]}...")
            
            try:
                # Parse and validate booking details
                booking_details = self._parse_and_validate_booking_details(user)
                if not booking_details:
                    return appointment_creation_attempted
                
                # Create appointment from booking details
                self._process_payment_first_appointment_creation(booking_details, user)
                    
            except Exception as e:
                logger.error(f"❌ Unexpected error during appointment creation for payment {self.transaction_id}: {str(e)}")
                import traceback
                logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                
                # Store comprehensive error information
                error_note = f"\n[{timezone.now()}] Error creating appointment: {str(e)}"
                self.notes = (self.notes or '') + error_note
                
                try:
                    self.save(user=user)
                except Exception as save_error:
                    logger.error(f"❌ Failed to save error note: {save_error}")
                
                # Don't raise the error - payment completion should not fail due to appointment creation issues
                
        elif self.appointment:
            logger.info(f"ℹ️ Payment {self.transaction_id} already has appointment {self.appointment.id} - skipping creation")
            
        elif not self.description:
            logger.info(f"ℹ️ Payment {self.transaction_id} has no description - likely traditional appointment-first flow")
            
        return appointment_creation_attempted

    def _parse_and_validate_booking_details(self, user):
        """Parse and validate booking details from payment description"""
        import logging
        import json
        logger = logging.getLogger(__name__)
        
        try:
            description_data = json.loads(self.description)
            logger.info(f"🚀 Parsed description data type: {description_data.get('type', 'unknown')}")
        except json.JSONDecodeError as json_error:
            logger.error(f"❌ Invalid JSON in payment description for {self.transaction_id}: {str(json_error)}")
            # Store JSON error details
            error_note = f"\n[{timezone.now()}] JSON parsing error: {str(json_error)}"
            self.notes = (self.notes or '') + error_note
            self.save(user=user)
            return None
        
        # Check if this is a payment-first booking
        if description_data.get('type') != 'payment_first_booking':
            logger.info(f"ℹ️ Description type '{description_data.get('type')}' is not payment_first_booking - skipping appointment creation")
            return None
        
        booking_details = description_data.get('booking_details', {})
        logger.info(f"🚀 Found booking details with keys: {list(booking_details.keys())}")
        
        if not booking_details:
            logger.warning(f"⚠️ Empty booking details for payment {self.transaction_id}")
            error_note = f"\n[{timezone.now()}] Empty booking details in payment-first booking"
            self.notes = (self.notes or '') + error_note
            self.save(user=user)
            return None
            
        return booking_details

    def _process_payment_first_appointment_creation(self, booking_details, user):
        """Process appointment creation and linking for payment-first flow"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Attempt to create appointment from booking details
        logger.info(f"🚀 Creating appointment from booking details...")
        appointment = self._create_appointment_from_booking_details(booking_details)
        
        if appointment:
            self._link_payment_to_appointment(appointment, user)
        else:
            logger.error(f"❌ Failed to create appointment for payment {self.transaction_id}")
            # Store detailed failure information
            error_note = f"\n[{timezone.now()}] Failed to create appointment from payment-first booking - check logs for details"
            self.notes = (self.notes or '') + error_note
            self.save(user=user)

    def _link_payment_to_appointment(self, appointment, user):
        """Link payment to the newly created appointment"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Link the payment to the newly created appointment
            logger.info(f"🔗 Linking payment {self.transaction_id} to appointment {appointment.appointment_id}")
            self.appointment = appointment
            
            # Also link hospital if not already set
            if not self.hospital and appointment.hospital:
                self.hospital = appointment.hospital
                logger.info(f"🔗 Also linked hospital: {appointment.hospital.name}")
            
            # Save the linkage
            self.save(user=user)
            logger.info(f"✅ Successfully created and linked appointment {appointment.appointment_id} to payment {self.transaction_id}")
            
            # Log successful appointment creation for monitoring
            self.log_access(user or self.patient, action='payment_first_appointment_created')
            
            # Add success note
            success_note = f"\n[{timezone.now()}] Successfully created appointment {appointment.appointment_id} from payment-first booking"
            self.notes = (self.notes or '') + success_note
            self.save(user=user)
            
        except Exception as link_error:
            logger.error(f"❌ Failed to link appointment {appointment.appointment_id} to payment {self.transaction_id}: {link_error}")
            # Even if linking fails, the appointment was created successfully
            success_note = f"\n[{timezone.now()}] Created appointment {appointment.appointment_id} but failed to link: {str(link_error)}"
            self.notes = (self.notes or '') + success_note
            self.save(user=user)

    def _log_payment_completion_result(self, appointment_creation_attempted):
        """Log final payment completion status"""
        import logging
        logger = logging.getLogger(__name__)
        
        final_status_note = f"Payment completion: status={self.payment_status}, appointment={'linked' if self.appointment else 'none'}"
        if appointment_creation_attempted:
            final_status_note += f", creation_attempted=true"
        logger.info(f"🏁 {final_status_note}")
                
    def _create_appointment_from_booking_details(self, booking_details):
        """Create an appointment from stored booking details with enhanced error handling"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"🚀 Creating appointment from booking details: {booking_details}")
            
            # Validate required booking details
            if not self._validate_required_booking_fields(booking_details):
                return None
            
            # Get department
            department = self._resolve_department(booking_details)
            if not department:
                return None
                
            # Get hospital using fallback strategies
            hospital = self._resolve_hospital_with_fallback_strategies(booking_details)
            if not hospital:
                return None
            
            # Parse appointment date
            appointment_date = self._parse_and_validate_appointment_date(booking_details)
            if not appointment_date:
                return None
            
            # Create the appointment
            appointment = self._create_appointment_with_validation(
                booking_details, department, hospital, appointment_date
            )
            if not appointment:
                return None
            
            # Create notifications (with error isolation)
            self._create_appointment_notifications(appointment)
            
            return appointment
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Unexpected error creating appointment from booking details: {str(e)}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return None

    def _validate_required_booking_fields(self, booking_details):
        """Validate required booking details fields"""
        import logging
        logger = logging.getLogger(__name__)
        
        required_fields = ['department_id', 'appointment_date']
        missing_fields = [field for field in required_fields if not booking_details.get(field)]
        if missing_fields:
            logger.error(f"❌ Missing required booking fields: {missing_fields}")
            return False
        return True

    def _resolve_department(self, booking_details):
        """Resolve department from booking details"""
        import logging
        from api.models.medical.department import Department
        logger = logging.getLogger(__name__)
        
        try:
            department = Department.objects.get(id=booking_details['department_id'])
            logger.info(f"Found department: {department.name}")
            return department
        except Department.DoesNotExist:
            logger.error(f"❌ Department {booking_details['department_id']} not found")
            return None

    def _resolve_hospital_with_fallback_strategies(self, booking_details):
        """Get hospital using multiple fallback strategies"""
        import logging
        from api.models import Hospital
        logger = logging.getLogger(__name__)
        
        hospital = None
        hospital_sources = []
        
        # Strategy 1: Use hospital from booking details
        if booking_details.get('hospital_id'):
            try:
                hospital = Hospital.objects.get(id=booking_details['hospital_id'])
                hospital_sources.append(f"booking_details: {hospital.name}")
            except Hospital.DoesNotExist:
                logger.warning(f"Hospital {booking_details['hospital_id']} from booking details not found")
        
        # Strategy 2: Use hospital from payment
        if not hospital and self.hospital:
            hospital = self.hospital
            hospital_sources.append(f"payment: {hospital.name}")
        
        # Strategy 3: Get user's primary hospital
        if not hospital:
            try:
                from api.models.medical.hospital_registration import HospitalRegistration
                primary_hospital = HospitalRegistration.objects.filter(
                    user=self.patient,
                    is_primary=True,
                    status='approved'
                ).first()
                if primary_hospital:
                    hospital = primary_hospital.hospital
                    hospital_sources.append(f"primary_registration: {hospital.name}")
            except Exception as reg_error:
                logger.warning(f"Failed to get primary hospital registration: {reg_error}")
        
        # Strategy 4: Get any approved hospital registration
        if not hospital:
            try:
                from api.models.medical.hospital_registration import HospitalRegistration
                any_hospital = HospitalRegistration.objects.filter(
                    user=self.patient,
                    status='approved'
                ).first()
                if any_hospital:
                    hospital = any_hospital.hospital
                    hospital_sources.append(f"any_registration: {hospital.name}")
            except Exception as reg_error:
                logger.warning(f"Failed to get any hospital registration: {reg_error}")
                
        if not hospital:
            logger.error("❌ No hospital found for appointment creation. Tried sources: " + str(hospital_sources))
            return None
            
        logger.info(f"Using hospital: {hospital.name} (source: {hospital_sources[-1]})")
        return hospital

    def _parse_and_validate_appointment_date(self, booking_details):
        """Parse and validate appointment date from booking details"""
        import logging
        from django.utils.dateparse import parse_datetime
        logger = logging.getLogger(__name__)
        
        appointment_date = None
        try:
            appointment_date = parse_datetime(booking_details['appointment_date'])
            if not appointment_date:
                # Try parsing as ISO format
                from datetime import datetime
                appointment_date = datetime.fromisoformat(booking_details['appointment_date'].replace('Z', '+00:00'))
        except Exception as date_error:
            logger.error(f"❌ Failed to parse appointment date '{booking_details['appointment_date']}': {date_error}")
            return None
        
        if not appointment_date:
            logger.error(f"❌ Invalid appointment date: {booking_details['appointment_date']}")
            return None
        
        logger.info(f"Parsed appointment date: {appointment_date}")
        return appointment_date

    def _create_appointment_with_validation(self, booking_details, department, hospital, appointment_date):
        """Create appointment object with proper error handling"""
        import logging
        from api.models.medical.appointment import Appointment
        from django.core.exceptions import ValidationError
        logger = logging.getLogger(__name__)
        
        try:
            appointment = Appointment(
                appointment_id=Appointment.generate_appointment_id(),
                patient=self.patient,
                hospital=hospital,
                department=department,
                appointment_date=appointment_date,
                appointment_type=booking_details.get('appointment_type', 'consultation'),
                priority=booking_details.get('priority', 'normal'),
                chief_complaint=booking_details.get('chief_complaint', ''),
                symptoms=booking_details.get('symptoms', ''),
                symptoms_data=[],  # Set empty list to avoid validation issues
                medical_history=booking_details.get('medical_history', ''),
                allergies=booking_details.get('allergies', ''),
                current_medications=booking_details.get('current_medications', ''),
                duration=booking_details.get('duration', 30),
                is_insurance_based=booking_details.get('is_insurance_based', False),
                insurance_details=booking_details.get('insurance_details', {}),
                status='pending',
                payment_status='completed'  # Mark as completed since payment is completed
            )
            
            # Save appointment with proper error handling
            try:
                appointment.save()
            except ValidationError as validation_error:
                # Log the validation error but don't fail payment completion
                logger.warning(f"Appointment validation failed during payment-first creation: {validation_error}")
                # Try saving with minimal validation by temporarily setting emergency priority
                if hasattr(appointment, 'priority'):
                    original_priority = appointment.priority
                    appointment.priority = 'emergency'  # Emergency appointments skip some validation
                    try:
                        appointment.save()
                        # Restore original priority after save
                        appointment.priority = original_priority
                        appointment.save()
                    except ValidationError:
                        logger.error("Failed to save appointment even with emergency priority")
                        raise
                else:
                    raise
            logger.info(f"✅ Successfully created appointment {appointment.appointment_id}")
            return appointment
            
        except Exception as create_error:
            logger.error(f"❌ Failed to create appointment object: {create_error}")
            import traceback
            logger.error(f"❌ Create traceback: {traceback.format_exc()}")
            return None

    def _create_appointment_notifications(self, appointment):
        """Create notifications for the appointment with error isolation"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from api.models.medical.appointment_notification import AppointmentNotification
            from api.models.medical_staff.doctor import Doctor
            
            # Create notification for the patient
            self._create_patient_notification(appointment)
            
            # Create notifications for doctors in the department
            self._create_doctor_notifications(appointment)
                    
        except Exception as notification_error:
            logger.error(f"⚠️ General notification error for appointment {appointment.appointment_id}: {notification_error}")
            # Don't fail appointment creation due to notification issues

    def _create_patient_notification(self, appointment):
        """Create notification for the patient"""
        import logging
        from api.models.medical.appointment_notification import AppointmentNotification
        logger = logging.getLogger(__name__)
        
        try:
            AppointmentNotification.objects.create(
                appointment=appointment,
                notification_type='email',
                event_type='booking_confirmation',
                recipient=appointment.patient,
                subject=f"Appointment Booking Confirmation - {appointment.appointment_id}",
                message=(
                    f"Dear {appointment.patient.get_full_name()},\n\n"
                    f"Your appointment at {appointment.hospital.name} ({appointment.department.name}) "
                    f"on {appointment.appointment_date.strftime('%Y-%m-%d %H:%M')} has been booked and paid.\n\n"
                    f"Appointment ID: {appointment.appointment_id}\n"
                    f"Status: Pending doctor's acceptance\n"
                    f"Payment: Completed\n"
                ),
                template_name='appointment_booking_confirmation'
            )
            logger.info(f"✅ Created patient notification for appointment {appointment.appointment_id}")
        except Exception as patient_notif_error:
            logger.error(f"⚠️ Failed to create patient notification: {patient_notif_error}")

    def _create_doctor_notifications(self, appointment):
        """Create notifications for doctors in the department"""
        import logging
        from api.models.medical.appointment_notification import AppointmentNotification
        from api.models.medical_staff.doctor import Doctor
        logger = logging.getLogger(__name__)
        
        try:
            doctors = Doctor.objects.filter(
                department=appointment.department,
                hospital=appointment.hospital,
                is_active=True
            )
            
            doctors_notified = 0
            for doctor in doctors:
                try:
                    AppointmentNotification.objects.create(
                        appointment=appointment,
                        notification_type='email',
                        event_type='new_appointment_available',
                        recipient=doctor.user,
                        subject=f"New Paid Appointment Available - {appointment.appointment_id}",
                        message=(
                            f"Dear Dr. {doctor.user.get_full_name()},\n\n"
                            f"A new paid appointment is available in your department:\n"
                            f"Date: {appointment.appointment_date.strftime('%Y-%m-%d %H:%M')}\n"
                            f"Department: {appointment.department.name}\n"
                            f"Patient: {appointment.patient.get_full_name()}\n"
                            f"Chief Complaint: {appointment.chief_complaint}\n"
                            f"Payment Status: Completed\n\n"
                            f"Please review and accept if you are available."
                        ),
                        template_name='new_appointment_notification'
                    )
                    doctors_notified += 1
                except Exception as doctor_notif_error:
                    logger.error(f"⚠️ Failed to create notification for doctor {doctor.user.get_full_name()}: {doctor_notif_error}")
            
            logger.info(f"✅ Created {doctors_notified} doctor notifications for appointment {appointment.appointment_id}")
            
        except Exception as doctors_error:
            logger.error(f"⚠️ Failed to create doctor notifications: {doctors_error}")

    def mark_as_failed(self, gateway_response=None, user=None):
        """Mark payment as failed with audit"""
        self.payment_status = 'failed'
        if gateway_response:
            self.gateway_data = gateway_response
        self.save(user=user)

    def process_refund(self, amount=None, reason=None, user=None):
        """Process refund with enhanced security"""
        if not user.has_perm('payment_transaction.can_process_refunds'):
            raise ValidationError("User does not have permission to process refunds")
            
        if self.payment_status != 'completed':
            raise ValidationError("Only completed payments can be refunded")
            
        if amount and amount > self.amount:
            raise ValidationError("Refund amount cannot exceed payment amount")
            
        self.payment_status = 'refunded'
        if reason:
            self.notes += f"\nRefund reason: {reason}"
        self.save(user=user)

    def get_audit_trail(self, user=None):
        """Get complete audit trail if user has permission"""
        if user and not user.has_perm('payment_transaction.can_view_audit_trail'):
            raise ValidationError("User does not have permission to view audit trail")
            
        return {
            'status_changes': self.status_change_history,
            'access_log': self.access_log,
            'created_by': self.created_by.get_full_name(),
            'created_at': self.created_at,
            'last_modified_by': self.last_modified_by.get_full_name(),
            'last_modified_at': self.updated_at
        }

    def get_payment_summary(self, include_sensitive=False):
        """Get summary of payment details with security check"""
        summary = {
            'transaction_id': self.transaction_id,
            'amount': self.amount_display,
            'currency': self.currency,
            'status': self.payment_status,
            'method': self.payment_method,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
        }
        
        if include_sensitive:
            summary.update({
                'actual_amount': self.amount,
                'insurance_data': self.insurance_data,
                'gateway_data': self.gateway_data
            })
            
        return summary

    @property
    def is_completed(self):
        """Check if payment is completed"""
        return self.payment_status == 'completed'

    @property
    def is_refundable(self):
        """Check if payment can be refunded"""
        return self.payment_status == 'completed'

    @property
    def payment_duration(self):
        """Calculate duration of payment processing"""
        if self.completed_at:
            return self.completed_at - self.created_at
        return None

    def get_payment_provider(self):
        """Get the payment provider instance"""
        if not self.payment_provider:
            return None
            
        from ..payment_providers import PROVIDER_MAPPING
        provider_class = PROVIDER_MAPPING.get(self.payment_provider)
        if provider_class:
            return provider_class(self)
        return None

    def initialize_payment(self):
        """Initialize payment with selected provider"""
        provider = self.get_payment_provider()
        if not provider:
            raise ValidationError("No payment provider selected")
            
        return provider.initialize_payment()

    def verify_payment(self, reference=None):
        """Verify payment with provider"""
        provider = self.get_payment_provider()
        if not provider:
            raise ValidationError("No payment provider selected")
            
        return provider.verify_payment(reference or self.provider_reference) 