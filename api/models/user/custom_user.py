# api/models/user/custom_user.py

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime, timedelta, timezone
import random
from .manager import CustomUserManager

class CustomUser(AbstractUser):
    # Override groups and user_permissions with custom related_names
    groups = models.ManyToManyField(
        'auth.Group',
        related_name="customuser_set",
        blank=True,
        help_text="The groups this user belongs to.",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name="customuser_set",
        blank=True,
        help_text="Specific permissions for this user.",
        related_query_name="customuser",
    )
    #  Roles for the user
    ROLES = [
    # Existing roles
    ('patient', 'Patient'),
    ('doctor', 'Doctor'),
    ('nurse', 'Nurse'),
    ('pharmacist', 'Pharmacist'),
    ('lab_technician', 'Laboratory Technician'),
    ('receptionist', 'Receptionist'),
    ('admin', 'Admin'),
    
    # Additional roles
    ('physician_assistant', 'Physician Assistant'),
    ('medical_secretary', 'Medical Secretary'),
    ('physical_therapist', 'Physical Therapist'),
    ('occupational_therapist', 'Occupational Therapist'),
    ('social_worker', 'Social Worker'),
    ('psychologist', 'Psychologist'),
    ('counselor', 'Counselor'),
    ('radiologist_tech', 'Radiology Technician'),
    ('dietitian', 'Dietitian/Nutritionist'),
    ('case_manager', 'Case Manager'),
    ('home_health_aide', 'Home Health Aide'),
    ('medical_records_clerk', 'Medical Records Clerk'),
    ('it_support', 'IT Support Specialist'),
    ('data_analyst', 'Health Data Analyst'),
    ('hospital_admin', 'Hospital Administrator'),
    ('insurance_coordinator', 'Insurance Coordinator'),
    ('billing_specialist', 'Billing Specialist'),
    ('patient_advocate', 'Patient Advocate'),
    ('compliance_officer', 'Compliance Officer'),
    ('clinical_researcher', 'Clinical Researcher'),
    ('biomedical_engineer', 'Biomedical Engineer'),
    ('paramedic', 'Paramedic'),
    ('emt', 'Emergency Medical Technician (EMT)'),
    ('midwife', 'Midwife'),
    ('dentist', 'Dentist'),
    ('dental_hygienist', 'Dental Hygienist'),
    ('medical_interpreter', 'Medical Interpreter'),
    ('speech_therapist', 'Speech-Language Pathologist'),
    ('pharmacy_tech', 'Pharmacy Technician'),
    ('infection_control', 'Infection Control Specialist'),
    ('qa_officer', 'Quality Assurance Officer'),
    ('volunteer_coordinator', 'Volunteer Coordinator'),
    ('hr_manager', 'Human Resources Manager'),
]
    role = models.CharField(
        max_length=30,
        choices=ROLES,
        default='patient'
    )

    # Extra fields for the user
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    nin = models.CharField(max_length=11, unique=True, null=True, blank=True)

    # Consent fields
    consent_terms = models.BooleanField(default=False)
    consent_hipaa = models.BooleanField(default=False)
    consent_data_processing = models.BooleanField(default=False)

    # HPN: Auto-generated Health Point Number, not editable in admin
    hpn = models.CharField(max_length=30, unique=True, editable=False, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True)
    password_reset_token = models.CharField(max_length=64, null=True, blank=True)
    social_provider = models.CharField(max_length=20, blank=True, null=True)
    social_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Check for on-boarding
    has_completed_onboarding = models.BooleanField(default=False)

    # Email verification
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(null=True, blank=True, unique=True)

    # OTP fields
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_required_for_login = models.BooleanField(default=True) # For security if the user wishes to toggle it on and off
    def generate_otp(self):
        self.otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.otp_created_at = datetime.now()
        self.save()
        return self.otp

    def verify_otp(self, otp):
        if not self.otp or not self.otp_created_at:
            return False
        
        current_time = datetime.now(timezone.utc)  # Add timezone
        time_diff = current_time - self.otp_created_at
        
        if time_diff > timedelta(minutes=5) or otp != self.otp:
            return False
            
        self.otp = None
        self.otp_created_at = None
        self.save()
        return True
    # Toggle OTP requirement (for security if the user wishes to toggle it on and off)
    def toggle_otp_requirement(self):
        self.otp_required_for_login = not self.otp_required_for_login
        self.save()

    # Primary hospital
    hospital = models.ForeignKey(
        'api.Hospital',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    gp_practice = models.ForeignKey(
        'api.GPPractice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    current_gp = models.ForeignKey(
        'api.GeneralPractitioner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_patients'
    )

    objects = CustomUserManager()

    # Use email as the unique identifier for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    email = models.EmailField(unique=True)

    def save(self, *args, **kwargs):
        # If username is not provided, set it to the email
        if not self.username:
            self.username = self.email
        # Auto-generate HPN if not set
        if not self.hpn:
            state_code = self.city[:3].upper() if self.city else "UNK"
            unique_number = str(uuid.uuid4().int)[:10]
            self.hpn = f"{state_code} {unique_number[:3]} {unique_number[3:6]} {unique_number[6:]}"
        super().save(*args, **kwargs)

    def register_with_hospital(self, hospital, is_primary=False):
        """
        Register user with a hospital
        """
        from api.models.medical.hospital_registration import HospitalRegistration
        
        registration = HospitalRegistration.objects.create(
            user=self,
            hospital=hospital,
            is_primary=is_primary
        )
        
        return registration

    def get_registered_hospitals(self):
        """
        Get all hospitals where the user is registered
        """
        return self.hospital_registrations.filter(status='approved')

    def set_primary_hospital(self, hospital):
        """
        Set a hospital as primary for the user
        """
        registration = self.hospital_registrations.filter(
            hospital=hospital,
            status='approved'
        ).first()
        
        if registration:
            # Update all other registrations to non-primary
            self.hospital_registrations.filter(is_primary=True).update(is_primary=False)
            
            # Set this registration as primary
            registration.is_primary = True
            registration.save()
            
            # Update user's primary hospital
            self.hospital = hospital
            self.save()
            return True
        return False