# api/models/medical/patient_admission.py

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid

from ..base import TimestampedModel

class PatientAdmission(TimestampedModel):
    """
    Model for tracking patient hospital admissions
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Admission'),
        ('admitted', 'Currently Admitted'),
        ('discharged', 'Discharged'),
        ('transferred', 'Transferred'),
        ('deceased', 'Deceased'),
        ('left_ama', 'Left Against Medical Advice'),
    ]
    
    PRIORITY_CHOICES = [
        ('emergency', 'Emergency'),
        ('urgent', 'Urgent'),
        ('elective', 'Elective'),
    ]
    
    ADMISSION_TYPE_CHOICES = [
        ('inpatient', 'Inpatient'),
        ('observation', 'Observation'),
        ('day_case', 'Day Case'),
        ('respite', 'Respite Care'),
    ]
    
    # Basic Information
    admission_id = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Unique admission identifier"
    )
    patient = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        related_name='admissions',
        null=True,  # Allow null for temporary patients
        blank=True,
        help_text="Patient being admitted"
    )
    
    # Temporary Patient Information
    is_registered_patient = models.BooleanField(
        default=True,
        help_text="Whether the patient was registered with the hospital before admission"
    )
    temp_patient_id = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        help_text="Temporary ID for unregistered patients"
    )
    temp_patient_details = models.JSONField(
        null=True, 
        blank=True,
        help_text="Temporary details for unregistered patients"
    )
    registration_status = models.CharField(
        max_length=20,
        choices=[
            ('complete', 'Complete Registration'),
            ('partial', 'Partial Registration'),
            ('pending', 'Registration Pending'),
        ],
        default='complete',
        help_text="Status of patient registration"
    )
    hospital = models.ForeignKey(
        'api.Hospital',
        on_delete=models.PROTECT,
        related_name='patient_admissions',
        help_text="Hospital where patient is admitted"
    )
    department = models.ForeignKey(
        'api.Department',
        on_delete=models.PROTECT,
        related_name='patient_admissions',
        help_text="Department where patient is admitted"
    )
    
    # Admission Details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current admission status"
    )
    admission_type = models.CharField(
        max_length=20,
        choices=ADMISSION_TYPE_CHOICES,
        default='inpatient',
        help_text="Type of admission"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='elective',
        help_text="Admission priority"
    )
    reason_for_admission = models.TextField(
        help_text="Primary reason for hospital admission"
    )
    
    # Bed Assignment
    is_icu_bed = models.BooleanField(
        default=False,
        help_text="Whether patient is in ICU bed"
    )
    bed_identifier = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Bed identifier (e.g., Room 101-A)"
    )
    
    # Doctor Assignment
    attending_doctor = models.ForeignKey(
        'api.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='attending_admissions',
        help_text="Primary doctor responsible for this patient"
    )
    consulting_doctors = models.ManyToManyField(
        'api.Doctor',
        related_name='consulting_admissions',
        blank=True,
        help_text="Other doctors consulting on this case"
    )
    
    # Timing Information
    admission_date = models.DateTimeField(
        default=timezone.now,
        help_text="When patient was admitted"
    )
    expected_discharge_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Expected discharge date"
    )
    actual_discharge_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual discharge date"
    )
    length_of_stay_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Length of stay in days (calculated on discharge)"
    )
    
    # Clinical Information
    diagnosis = models.TextField(
        blank=True,
        help_text="Primary diagnosis"
    )
    secondary_diagnoses = models.TextField(
        blank=True,
        help_text="Secondary diagnoses"
    )
    acuity_level = models.PositiveSmallIntegerField(
        default=3,
        help_text="Patient acuity level (1-5, with 5 being highest acuity)"
    )
    isolation_required = models.BooleanField(
        default=False,
        help_text="Whether patient requires isolation"
    )
    isolation_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of isolation if required"
    )
    
    # Discharge Information
    discharge_destination = models.CharField(
        max_length=100,
        blank=True,
        help_text="Where patient was discharged to"
    )
    discharge_summary = models.TextField(
        blank=True,
        help_text="Summary of stay and discharge instructions"
    )
    followup_instructions = models.TextField(
        blank=True,
        help_text="Follow-up care instructions"
    )
    
    # Administrative
    insurance_information = models.JSONField(
        default=dict,
        blank=True,
        help_text="Insurance details for this admission"
    )
    admission_notes = models.TextField(
        blank=True,
        help_text="Administrative notes about this admission"
    )
    
    def __str__(self):
        patient_name = self.patient.get_full_name() if self.patient else self.temp_patient_details.get('full_name', 'Unregistered Patient')
        return f"{self.admission_id} - {patient_name}"

    @property
    def patient_name(self):
        """Return patient name, either from user account or temp details"""
        if self.patient:
            return self.patient.get_full_name()
        elif self.temp_patient_details:
            return f"{self.temp_patient_details.get('first_name', '')} {self.temp_patient_details.get('last_name', '')}"
        return 'Unknown Patient'
        
    def generate_temp_patient_id(self):
        """Generate a temporary patient ID for emergency admissions"""
        date_str = timezone.now().strftime('%y%m%d')
        random_part = str(uuid.uuid4())[:4].upper()
        return f"TEMP-{date_str}-{random_part}"
        
    def convert_to_registered_patient(self, user_data):
        """Convert a temporary patient to a registered patient with HPN number"""
        from api.models import CustomUser, HospitalRegistration
        
        # Only proceed if this is a temporary admission
        if self.is_registered_patient:
            return False
            
        # Create user account with data from admission
        # Generate a unique username based on email with a random suffix to avoid collisions
        import uuid
        email = user_data['email']
        username = email.split('@')[0] + '_' + str(uuid.uuid4())[:8]
        
        # Prepare user data including city for proper HPN generation
        user_kwargs = {
            'username': username,
            'email': email,
            'password': user_data.get('password', CustomUser.objects.make_random_password()),
            'first_name': self.temp_patient_details.get('first_name', ''),
            'last_name': self.temp_patient_details.get('last_name', ''),
            'phone': self.temp_patient_details.get('phone_number', ''),
            'date_of_birth': user_data.get('date_of_birth', None)
        }
        
        # Ensure city is included for HPN generation
        if 'city' in self.temp_patient_details:
            user_kwargs['city'] = self.temp_patient_details.get('city')
        elif 'address' in self.temp_patient_details:
            address_parts = self.temp_patient_details.get('address', '').split(',')
            if len(address_parts) > 1:
                user_kwargs['city'] = address_parts[1].strip()
        
        # Create user with all fields including city
        user = CustomUser.objects.create_user(**user_kwargs)
        
        # The HPN should have been automatically generated during user creation
        # since we included the city in the create_user kwargs
        
        # Store the HPN in temp_patient_details for reference
        self.temp_patient_details['hpn_number'] = user.hpn
        
        # Create hospital registration
        registration = HospitalRegistration.objects.create(
            user=user,
            hospital=self.hospital,
            is_primary=True,
            status='approved'  # Auto-approve since they're already admitted
        )
        
        # Update admission record
        self.patient = user
        self.is_registered_patient = True
        self.registration_status = 'complete'
        # Keep temp_patient_details for record purposes
        self.save()
        
        # TODO: Send welcome email with credentials
        # This would call an email utility function
        
        return user

    class Meta:
        indexes = [
            models.Index(fields=['admission_id']),
            models.Index(fields=['patient']),
            models.Index(fields=['status']),
            models.Index(fields=['hospital', 'department']),
            models.Index(fields=['admission_date']),
            models.Index(fields=['attending_doctor']),
        ]
        ordering = ['-admission_date']

    def save(self, *args, **kwargs):
        # Generate admission ID if not provided
        if not self.admission_id:
            from api.utils.id_generators import generate_admission_id
            self.admission_id = generate_admission_id()
            
        # Handle bed assignment/release based on status changes
        if self._state.adding:  # New admission
            if getattr(self, '_assign_bed_on_create', False):
                self.status = 'admitted'
                self._assign_bed()
            elif self.status == 'admitted':
                self._assign_bed()
        else:
            original = PatientAdmission.objects.get(pk=self.pk)
            if original.status != self.status:
                if self.status == 'admitted' and original.status != 'admitted':
                    self._assign_bed()
                elif self.status != 'admitted' and original.status == 'admitted':
                    self._release_bed()
                    
                # Calculate length of stay on discharge
                if self.status in ['discharged', 'deceased', 'transferred', 'left_ama'] and not self.actual_discharge_date:
                    self.actual_discharge_date = timezone.now()
                    if self.admission_date:
                        delta = self.actual_discharge_date - self.admission_date
                        self.length_of_stay_days = delta.days + (1 if delta.seconds > 0 else 0)
        
        super().save(*args, **kwargs)
    
    def _assign_bed(self):
        """Assign a bed in the department"""
        if self.department:
            self.department.assign_bed(is_icu=self.is_icu_bed)
            self.department.current_patient_count += 1
            self.department.save()
    
    def _release_bed(self):
        """Release the bed when patient is discharged/transferred"""
        if self.department:
            self.department.release_bed(is_icu=self.is_icu_bed)
            if self.department.current_patient_count > 0:
                self.department.current_patient_count -= 1
                self.department.save()
    
    def admit_patient(self):
        """Admit a pending patient"""
        if self.status != 'pending':
            raise ValidationError("Can only admit patients with pending status")
        self.status = 'admitted'
        self._assign_bed()
        self.save()
        return True
    
    def discharge_patient(self, destination="", summary="", followup=""):
        """Discharge an admitted patient"""
        if self.status != 'admitted':
            raise ValidationError("Can only discharge patients who are currently admitted")
        self.status = 'discharged'
        self.discharge_destination = destination
        self.discharge_summary = summary
        self.followup_instructions = followup
        self.actual_discharge_date = timezone.now()
        self.save()
        return True
    
    def transfer_patient(self, new_department, new_doctor=None, is_icu=None, reason=""):
        """Transfer patient to another department"""
        if self.status != 'admitted':
            raise ValidationError("Can only transfer patients who are currently admitted")
            
        # Release current bed
        self._release_bed()
        
        # Update department and ICU status if provided
        old_department = self.department
        self.department = new_department
        if is_icu is not None:
            self.is_icu_bed = is_icu
        if new_doctor:
            self.attending_doctor = new_doctor
            
        # Assign new bed
        self._assign_bed()
        
        # Create transfer record
        from .patient_transfer import PatientTransfer
        PatientTransfer.objects.create(
            admission=self,
            from_department=old_department,
            to_department=new_department,
            reason=reason
        )
        
        self.save()
        return True
    
    @property
    def current_length_of_stay(self):
        """Calculate current length of stay in days"""
        if self.actual_discharge_date:
            delta = self.actual_discharge_date - self.admission_date
        else:
            delta = timezone.now() - self.admission_date
        return delta.days + (1 if delta.seconds > 0 else 0)
    
    @property
    def is_active(self):
        """Check if admission is currently active"""
        return self.status in ['pending', 'admitted']
