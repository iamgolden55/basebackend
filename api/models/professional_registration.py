"""
Professional Registration Models

Models for managing professional healthcare worker registration,
licensing, and verification in the PHB system.
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid
import random


class ProfessionalApplication(models.Model):
    """
    Professional Registration Application

    Tracks healthcare professionals applying for PHB registration.
    Applications go through review workflow: draft → submitted → under_review → approved/rejected
    """

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    PROFESSIONAL_TYPES = [
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('pharmacist', 'Pharmacist'),
        ('lab_technician', 'Laboratory Technician'),
        ('radiographer', 'Radiographer'),
        ('physiotherapist', 'Physiotherapist'),
        ('dentist', 'Dentist'),
        ('optometrist', 'Optometrist'),
        ('midwife', 'Midwife'),
        ('paramedic', 'Paramedic'),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application_reference = models.CharField(max_length=20, unique=True, editable=False)

    # User association
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='professional_applications')

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)

    # Professional Details
    professional_type = models.CharField(max_length=50, choices=PROFESSIONAL_TYPES)
    regulatory_body = models.CharField(max_length=200, help_text="e.g., Medical and Dental Council of Nigeria")
    regulatory_body_registration_number = models.CharField(max_length=100, help_text="Original registration number from regulatory body")

    # Educational Qualification
    qualification = models.CharField(max_length=200, help_text="e.g., MBBS, BSc Nursing")
    institution = models.CharField(max_length=200, help_text="Institution where qualification was obtained")
    graduation_year = models.IntegerField()

    # Work Experience
    years_of_experience = models.IntegerField(default=0)
    current_employer = models.CharField(max_length=200, blank=True)
    current_position = models.CharField(max_length=200, blank=True)

    # Specialization (optional)
    specialization = models.CharField(max_length=200, blank=True)

    # Application Status & Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='reviewed_applications')
    review_started_at = models.DateTimeField(null=True, blank=True)
    review_completed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    # Rejection details
    rejection_reason = models.TextField(blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    # Documents tracking
    documents_verified = models.BooleanField(default=False)
    documents_verification_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'professional_type']),
            models.Index(fields=['application_reference']),
            models.Index(fields=['regulatory_body_registration_number']),
        ]

    def __str__(self):
        return f"{self.application_reference} - {self.first_name} {self.last_name} ({self.professional_type})"

    def save(self, *args, **kwargs):
        # Auto-generate application reference if not exists
        if not self.application_reference:
            self.application_reference = self._generate_reference()
        super().save(*args, **kwargs)

    def _generate_reference(self):
        """Generate unique application reference number"""
        prefix = "APP"
        timestamp = timezone.now().strftime("%y%m")
        random_num = random.randint(1000, 9999)
        return f"{prefix}-{timestamp}-{random_num}"

    def submit(self):
        """Mark application as submitted"""
        if self.status == 'draft':
            self.status = 'submitted'
            self.submitted_at = timezone.now()
            self.save()

    def start_review(self, reviewer):
        """Start reviewing the application"""
        if self.status == 'submitted':
            self.status = 'under_review'
            self.reviewed_by = reviewer
            self.review_started_at = timezone.now()
            self.save()

    def approve(self, reviewer, notes=''):
        """Approve the application"""
        if self.status == 'under_review':
            self.status = 'approved'
            self.reviewed_by = reviewer
            self.review_completed_at = timezone.now()
            self.review_notes = notes
            self.save()

    def reject(self, reviewer, reason):
        """Reject the application"""
        if self.status in ['submitted', 'under_review']:
            self.status = 'rejected'
            self.reviewed_by = reviewer
            self.rejected_at = timezone.now()
            self.rejection_reason = reason
            self.save()


class RegistryEntry(models.Model):
    """
    PHB Professional Registry

    Official registry of verified healthcare professionals with PHB licenses.
    Created when an application is approved.
    """

    LICENSE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
        ('expired', 'Expired'),
    ]

    PRACTICE_TYPES = [
        ('public', 'Public Sector'),
        ('private', 'Private Practice'),
        ('both', 'Both Public and Private'),
        ('research', 'Research/Academic'),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license_number = models.CharField(max_length=20, unique=True, db_index=True)

    # Link to original application
    application = models.OneToOneField(ProfessionalApplication, on_delete=models.PROTECT, related_name='registry_entry')

    # Professional identification
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='registry_entries')
    professional_type = models.CharField(max_length=50)
    full_name = models.CharField(max_length=200)

    # License details
    license_status = models.CharField(max_length=20, choices=LICENSE_STATUS_CHOICES, default='active')
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    # Practice information
    practice_type = models.CharField(max_length=20, choices=PRACTICE_TYPES, default='public')
    primary_facility = models.CharField(max_length=200, blank=True)

    # Public profile (shown in public registry search)
    public_email = models.EmailField(blank=True)
    public_phone = models.CharField(max_length=20, blank=True)
    biography = models.TextField(blank=True)
    specializations = models.TextField(blank=True, help_text="Comma-separated list")

    # Regulatory compliance
    regulatory_body = models.CharField(max_length=200)
    regulatory_registration_number = models.CharField(max_length=100)

    # Verification & Quality
    verification_level = models.CharField(max_length=20, default='verified',
                                         choices=[('verified', 'Verified'), ('premium', 'Premium Verified')])
    verification_date = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='verified_professionals')

    # Status tracking
    suspension_reason = models.TextField(blank=True)
    suspension_date = models.DateTimeField(null=True, blank=True)
    suspended_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='suspended_professionals')

    revocation_reason = models.TextField(blank=True)
    revocation_date = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='revoked_professionals')

    # Reactivation tracking
    reactivation_date = models.DateTimeField(null=True, blank=True)
    reactivation_notes = models.TextField(blank=True)
    reactivated_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='reactivated_professionals')

    # Renewal tracking
    last_renewed_at = models.DateTimeField(null=True, blank=True)
    renewal_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Registry Entry'
        verbose_name_plural = 'Registry Entries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['license_number']),
            models.Index(fields=['license_status', 'professional_type']),
            models.Index(fields=['regulatory_registration_number']),
        ]

    def __str__(self):
        return f"{self.license_number} - {self.full_name} ({self.professional_type})"

    def save(self, *args, **kwargs):
        # Auto-generate license number if not exists
        if not self.license_number:
            self.license_number = self._generate_license_number()
        super().save(*args, **kwargs)

    def _generate_license_number(self):
        """Generate unique PHB license number"""
        type_prefix = {
            'doctor': 'DOC',
            'nurse': 'NUR',
            'pharmacist': 'PHA',
            'lab_technician': 'LAB',
            'radiographer': 'RAD',
            'physiotherapist': 'PHY',
            'dentist': 'DEN',
            'optometrist': 'OPT',
            'midwife': 'MID',
            'paramedic': 'PAR',
        }.get(self.professional_type, 'PRO')

        timestamp = timezone.now().strftime("%y%m")
        random_num = random.randint(10000, 99999)
        return f"PHB-{type_prefix}-{timestamp}{random_num}"

    def suspend(self, reason, admin_user):
        """Suspend the license"""
        self.license_status = 'suspended'
        self.suspension_reason = reason
        self.suspension_date = timezone.now()
        self.suspended_by = admin_user
        self.save()

    def reactivate(self, admin_user, notes=''):
        """Reactivate a suspended license"""
        if self.license_status == 'suspended':
            self.license_status = 'active'
            self.reactivation_date = timezone.now()
            self.reactivation_notes = notes
            self.reactivated_by = admin_user
            # Clear suspension details
            self.suspension_reason = ''
            self.suspension_date = None
            self.save()

    def revoke(self, reason, admin_user):
        """Revoke the license permanently"""
        self.license_status = 'revoked'
        self.revocation_reason = reason
        self.revocation_date = timezone.now()
        self.revoked_by = admin_user
        self.save()

    def renew(self, years=1):
        """Renew the license"""
        self.expires_at = timezone.now() + timedelta(days=365 * years)
        self.last_renewed_at = timezone.now()
        self.renewal_count += 1
        if self.license_status == 'expired':
            self.license_status = 'active'
        self.save()

    def is_expired(self):
        """Check if license is expired"""
        return self.expires_at < timezone.now()


class DisciplinaryRecord(models.Model):
    """
    Disciplinary records for professionals

    Tracks any disciplinary actions or complaints against registered professionals.
    """

    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('serious', 'Serious'),
        ('critical', 'Critical'),
    ]

    INCIDENT_TYPES = [
        ('complaint', 'Patient Complaint'),
        ('malpractice', 'Medical Malpractice'),
        ('misconduct', 'Professional Misconduct'),
        ('ethics', 'Ethics Violation'),
        ('negligence', 'Negligence'),
        ('fraud', 'Fraud'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registry_entry = models.ForeignKey(RegistryEntry, on_delete=models.CASCADE, related_name='disciplinary_records')

    # Incident details
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPES)
    description = models.TextField()
    incident_date = models.DateField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)

    # Action taken
    action_taken = models.TextField()
    suspension_period_days = models.IntegerField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Case details
    case_reference = models.CharField(max_length=100, blank=True)
    reported_by = models.CharField(max_length=200, blank=True)

    # Resolution
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Admin tracking
    created_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-incident_date']

    def __str__(self):
        return f"{self.registry_entry.license_number} - {self.incident_type} ({self.incident_date})"
