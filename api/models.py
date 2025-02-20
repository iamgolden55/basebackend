# api/models.py

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from django.contrib.auth import authenticate
from datetime import datetime, timedelta, timezone
import random

# --- Custom User Manager ---
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)

# --- Supporting Models ---
class Hospital(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)  # For admin verification

    def __str__(self):
        return self.name

class GPPractice(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    hospital = models.ForeignKey(
        Hospital, on_delete=models.SET_NULL, null=True, blank=True, related_name='gp_practices'
    )

    def __str__(self):
        return self.name

class GeneralPractitioner(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    practice = models.ForeignKey(
        GPPractice, on_delete=models.SET_NULL, null=True, blank=True, related_name='general_practitioners'
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# --- Custom User Model ---
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
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(
        max_length=20, 
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
    primary_hospital = models.ForeignKey(
        Hospital, on_delete=models.SET_NULL, null=True, blank=True
    )
    current_gp_practice = models.ForeignKey(
        GPPractice, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_patients'
    )
    current_gp = models.ForeignKey(
        GeneralPractitioner, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_patients'
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

# --- Medical Record Model ---
class MedicalRecord(models.Model):
    # We use the HPN as the central identifier.
    hpn = models.CharField(max_length=30, unique=True)
    # Optionally link to the user (nullable, in case of anonymization)
    user = models.OneToOneField(
    CustomUser,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='medical_record'
)
    is_anonymous = models.BooleanField(default=False)  # Flag for anonymization

    # Medical details
    blood_type = models.CharField(
        max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        null=True, blank=True
    )
    allergies = models.TextField(null=True, blank=True)
    chronic_conditions = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, null=True, blank=True)
    is_high_risk = models.BooleanField(default=False)
    last_visit_date = models.DateTimeField(null=True, blank=True)

    def anonymize_record(self):
        """Mark the record as anonymous and disassociate it from the user."""
        self.is_anonymous = True
        self.user = None
        self.save()

    def __str__(self):
        return f"Medical Record for HPN: {self.hpn}"

# --- Signals ---

@receiver(post_save, sender=CustomUser)
def create_medical_record(sender, instance, created, **kwargs):
    if created:
        # Automatically create a MedicalRecord linked to the user's HPN
        MedicalRecord.objects.create(hpn=instance.hpn, user=instance)

@receiver(pre_delete, sender=CustomUser)
def handle_related_deletions(sender, instance, **kwargs):
    try:
        with transaction.atomic():
            # Anonymize medical records if they exist
            if hasattr(instance, 'medical_record'):
                record = instance.medical_record
                if record:
                    record.anonymize_record()

            # Delete or blacklist tokens associated with the user
            tokens = OutstandingToken.objects.filter(user=instance)
            tokens.delete()  # Ensures tokens do not block deletion

    except Exception as e:
        print(f"Error handling related deletions: {e}")