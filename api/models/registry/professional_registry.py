"""
PHB Professional Registry Models

Public searchable registry of all licensed professionals (similar to GMC Public Register).
This registry allows patients and hospitals to verify professional credentials.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid
from ..base import TimestampedModel

User = get_user_model()


class PHBProfessionalRegistry(TimestampedModel):
    """
    PHB National Professional Registry (Public Register).

    Similar to GMC's public "List of Registered Medical Practitioners".
    This is a public-facing record that allows anyone to verify a professional's
    license status and credentials.

    Created automatically when ProfessionalApplication is approved.
    """

    LICENSE_STATUS = [
        ('active', 'Active - Licensed to Practice'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired - Renewal Required'),
        ('revoked', 'Revoked'),
        ('inactive', 'Inactive - Voluntarily Not Practicing'),
    ]

    PROFESSIONAL_TYPE = [
        ('doctor', 'Medical Doctor'),
        ('pharmacist', 'Pharmacist'),
        ('nurse', 'Nurse'),
        ('physiotherapist', 'Physiotherapist'),
        ('lab_technician', 'Laboratory Technician'),
        ('radiographer', 'Radiographer'),
        ('midwife', 'Midwife'),
        ('dentist', 'Dentist'),
        ('optometrist', 'Optometrist'),
    ]

    # Identification
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for registry entry'
    )

    # Link to User and Application
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='professional_registry',
        help_text='User account linked to this professional'
    )
    application = models.OneToOneField(
        'ProfessionalApplication',
        on_delete=models.CASCADE,
        related_name='registry_entry',
        help_text='Approved application that created this registry entry'
    )

    # Professional Information (Public)
    phb_license_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='PHB professional license number (e.g., PHB-DOC-2025-00123)'
    )
    professional_type = models.CharField(
        max_length=30,
        choices=PROFESSIONAL_TYPE,
        db_index=True,
        help_text='Type of professional'
    )

    # Name (Public)
    title = models.CharField(max_length=10, help_text='Professional title (Dr., Mr., etc.)')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # Qualifications (Public)
    primary_qualification = models.CharField(
        max_length=255,
        help_text='Primary degree (e.g., MBBS, BPharm, etc.)'
    )
    qualification_year = models.PositiveIntegerField(help_text='Year of qualification')
    specialization = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text='Area of specialization'
    )

    # License Information (Public)
    license_status = models.CharField(
        max_length=20,
        choices=LICENSE_STATUS,
        default='active',
        db_index=True,
        help_text='Current status of the professional license'
    )
    license_issue_date = models.DateField(help_text='Date license was first issued')
    license_expiry_date = models.DateField(
        help_text='Current license expiry date (requires annual renewal)'
    )
    last_renewal_date = models.DateField(
        null=True,
        blank=True,
        help_text='Last license renewal date'
    )

    # Home Registration (Public - for transparency)
    home_registration_body = models.CharField(
        max_length=255,
        blank=True,
        help_text='Primary registration body (e.g., GMC, MDCN, etc.)'
    )
    home_registration_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Registration number with primary body'
    )

    # Practice Settings (Public)
    practice_type = models.CharField(
        max_length=30,
        choices=[
            ('hospital', 'Hospital-based Only'),
            ('private', 'Private Practice Only'),
            ('both', 'Both Hospital and Private'),
            ('not_practicing', 'Not Currently Practicing'),
        ],
        default='hospital',
        help_text='Current practice setting'
    )

    # Location (Public - for searchability)
    city = models.CharField(
        max_length=100,
        db_index=True,
        help_text='City where professional is based'
    )
    state = models.CharField(
        max_length=100,
        db_index=True,
        help_text='State/region'
    )
    country = models.CharField(max_length=100, default='Nigeria')

    # Languages (Public)
    languages_spoken = models.CharField(
        max_length=255,
        blank=True,
        help_text='Languages spoken (comma-separated)'
    )

    # Public Contact (Optional - professional can choose to list)
    public_email = models.EmailField(
        blank=True,
        help_text='Public email for professional inquiries (optional)'
    )
    public_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Public phone number (optional)'
    )
    website = models.URLField(
        blank=True,
        help_text='Professional website (optional)'
    )

    # Verification Status
    identity_verified = models.BooleanField(
        default=True,
        help_text='Identity has been verified by PHB'
    )
    qualifications_verified = models.BooleanField(
        default=True,
        help_text='Qualifications verified by PHB'
    )

    # Disciplinary Records (Public - for transparency)
    has_disciplinary_record = models.BooleanField(
        default=False,
        help_text='Whether professional has any disciplinary sanctions'
    )
    disciplinary_notes = models.TextField(
        blank=True,
        help_text='Public record of any sanctions or restrictions (if applicable)'
    )

    # Status Change Tracking
    status_changed_date = models.DateField(
        null=True,
        blank=True,
        help_text='Last date status was changed (suspension, revocation, etc.)'
    )
    status_change_reason = models.TextField(
        blank=True,
        help_text='Reason for status change (if applicable)'
    )

    # Public Visibility
    is_searchable = models.BooleanField(
        default=True,
        help_text='Whether this entry appears in public registry search'
    )

    # Additional Information
    biography = models.TextField(
        blank=True,
        help_text='Optional professional biography (public)'
    )
    areas_of_interest = models.TextField(
        blank=True,
        help_text='Clinical interests or areas of expertise (public)'
    )

    # Metadata
    first_registered_date = models.DateField(
        auto_now_add=True,
        help_text='Date first added to PHB registry'
    )

    class Meta:
        db_table = 'phb_professional_registry'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['phb_license_number'], name='idx_reg_license'),
            models.Index(fields=['professional_type', 'license_status'], name='idx_reg_type_status'),
            models.Index(fields=['license_status', 'license_expiry_date'], name='idx_reg_status_expiry'),
            models.Index(fields=['specialization', 'license_status'], name='idx_reg_spec_status'),
            models.Index(fields=['city', 'state'], name='idx_reg_location'),
            models.Index(fields=['last_name', 'first_name'], name='idx_reg_name'),
            models.Index(fields=['is_searchable', 'license_status'], name='idx_reg_searchable'),
        ]
        verbose_name = 'PHB Professional Registry Entry'
        verbose_name_plural = 'PHB Professional Registry Entries'

    def __str__(self):
        return f"{self.get_full_name()} ({self.phb_license_number}) - {self.get_professional_type_display()}"

    def get_full_name(self):
        """Get professional's full name with title"""
        return f"{self.title} {self.first_name} {self.last_name}"

    @property
    def is_active(self):
        """Check if license is currently active"""
        return self.license_status == 'active'

    @property
    def is_expired(self):
        """Check if license has expired"""
        from datetime import date
        return self.license_expiry_date < date.today()

    @property
    def days_until_expiry(self):
        """Get number of days until license expires"""
        from datetime import date
        delta = self.license_expiry_date - date.today()
        return delta.days

    @property
    def requires_renewal(self):
        """Check if license is approaching expiry (within 30 days)"""
        return self.days_until_expiry <= 30 and self.days_until_expiry >= 0

    def suspend_license(self, reason, admin_user):
        """Suspend professional's license"""
        self.license_status = 'suspended'
        self.status_changed_date = timezone.now().date()
        self.status_change_reason = f"Suspended by {admin_user.get_full_name()}: {reason}"
        self.save(update_fields=[
            'license_status', 'status_changed_date', 'status_change_reason', 'updated_at'
        ])

    def revoke_license(self, reason, admin_user):
        """Permanently revoke professional's license"""
        self.license_status = 'revoked'
        self.status_changed_date = timezone.now().date()
        self.status_change_reason = f"Revoked by {admin_user.get_full_name()}: {reason}"
        self.is_searchable = False  # Remove from public search
        self.save(update_fields=[
            'license_status', 'status_changed_date', 'status_change_reason',
            'is_searchable', 'updated_at'
        ])

    def renew_license(self):
        """Renew professional's license for another year"""
        from datetime import timedelta

        self.license_status = 'active'
        self.last_renewal_date = timezone.now().date()
        self.license_expiry_date = (timezone.now() + timedelta(days=365)).date()
        self.save(update_fields=[
            'license_status', 'last_renewal_date', 'license_expiry_date', 'updated_at'
        ])

    def reactivate_license(self, admin_user):
        """Reactivate a suspended license"""
        if self.license_status != 'suspended':
            raise ValueError('Only suspended licenses can be reactivated')

        self.license_status = 'active'
        self.status_changed_date = timezone.now().date()
        self.status_change_reason = f"Reactivated by {admin_user.get_full_name()}"
        self.save(update_fields=[
            'license_status', 'status_changed_date', 'status_change_reason', 'updated_at'
        ])

    def set_inactive(self):
        """Set license to inactive (voluntary non-practice)"""
        self.license_status = 'inactive'
        self.status_changed_date = timezone.now().date()
        self.status_change_reason = "Professional chose to set license as inactive"
        self.save(update_fields=[
            'license_status', 'status_changed_date', 'status_change_reason', 'updated_at'
        ])

    def add_disciplinary_record(self, notes, admin_user):
        """Add a disciplinary sanction to public record"""
        self.has_disciplinary_record = True
        timestamp = timezone.now().strftime('%Y-%m-%d')
        new_note = f"[{timestamp}] {notes}"

        if self.disciplinary_notes:
            self.disciplinary_notes += f"\n\n{new_note}"
        else:
            self.disciplinary_notes = new_note

        self.save(update_fields=['has_disciplinary_record', 'disciplinary_notes', 'updated_at'])
