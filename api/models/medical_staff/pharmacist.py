# api/models/medical_staff/pharmacist.py

import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..user.custom_user import CustomUser
from ..medical.hospital import Hospital
from ..base import TimestampedModel

User = get_user_model()


class Pharmacist(TimestampedModel):
    """
    Pharmacist model representing clinical pharmacists in the hospital.
    Handles pharmacist information, prescribing authority, and triage capabilities.
    """

    # Prescribing Authority Levels (based on UK/NHS model)
    PRESCRIBING_AUTHORITY_CHOICES = [
        ('none', 'No Prescribing Authority'),
        ('supplementary', 'Supplementary Prescriber'),  # Under CPA with physician
        ('independent', 'Independent Prescriber'),      # Full prescribing authority
        ('community', 'Community Pharmacist Prescriber'),  # Limited to specific conditions
    ]

    # Controlled Substance Levels
    CONTROLLED_SUBSTANCE_LEVELS = [
        ('none', 'Cannot Prescribe Controlled Substances'),
        ('schedule_3_5', 'Schedules 3-5 Only'),  # Less restrictive controlled substances
        ('all_schedules', 'All Schedules'),      # Full controlled substance authority
    ]

    # Triage Specialties
    TRIAGE_SPECIALTIES = [
        ('general', 'General Pharmacy'),
        ('cardiology', 'Cardiovascular Medications'),
        ('diabetes', 'Diabetes & Endocrine'),
        ('mental_health', 'Mental Health Medications'),
        ('pediatrics', 'Pediatric Pharmacy'),
        ('geriatrics', 'Geriatric Pharmacy'),
        ('oncology', 'Oncology Pharmacy'),
        ('infectious_disease', 'Infectious Disease'),
        ('pain_management', 'Pain & Palliative Care'),
        ('respiratory', 'Respiratory Medications'),
    ]

    # Basic Information
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for pharmacist"
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='pharmacist_profile',
        help_text="User account associated with this pharmacist"
    )
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pharmacists',
        help_text="Primary hospital affiliation (if hospital pharmacist)"
    )

    # Professional Information
    pharmacy_license_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Pharmacy license registration number"
    )
    license_expiry_date = models.DateField(
        help_text="Pharmacy license expiry date"
    )
    years_of_experience = models.PositiveIntegerField(
        help_text="Years of professional pharmacy experience"
    )
    qualifications = models.JSONField(
        default=list,
        blank=True,
        help_text="List of pharmacy qualifications (PharmD, MSc, etc.)"
    )
    board_certifications = models.TextField(
        null=True,
        blank=True,
        help_text="Pharmacy board certifications (e.g., BCPS, BCACP)"
    )

    # Prescribing Authority
    can_review_prescriptions = models.BooleanField(
        default=True,
        help_text="Whether pharmacist can review and approve prescription requests"
    )
    prescribing_authority_level = models.CharField(
        max_length=20,
        choices=PRESCRIBING_AUTHORITY_CHOICES,
        default='supplementary',
        help_text="Level of prescribing authority"
    )
    can_prescribe_controlled = models.BooleanField(
        default=False,
        help_text="Whether pharmacist can prescribe controlled substances"
    )
    controlled_substance_level = models.CharField(
        max_length=20,
        choices=CONTROLLED_SUBSTANCE_LEVELS,
        default='none',
        help_text="Level of controlled substance prescribing authority"
    )
    collaborative_practice_agreement = models.BooleanField(
        default=False,
        help_text="Whether pharmacist has CPA with supervising physician"
    )
    supervising_physician = models.ForeignKey(
        'Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_pharmacists',
        help_text="Physician overseeing pharmacist's prescribing activities (for CPA)"
    )

    # Triage and Specialty
    triage_specialty = models.CharField(
        max_length=30,
        choices=TRIAGE_SPECIALTIES,
        default='general',
        help_text="Pharmacist's specialty for triage assignment"
    )
    auto_assign_triage = models.BooleanField(
        default=True,
        help_text="Whether to auto-assign prescription requests to this pharmacist"
    )
    max_daily_reviews = models.PositiveIntegerField(
        default=30,
        help_text="Maximum prescription reviews per day"
    )

    # Availability Management
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the pharmacist is currently practicing"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('on_leave', 'On Leave'),
            ('suspended', 'Suspended'),
            ('retired', 'Retired')
        ],
        default='active',
        help_text="Current working status"
    )
    available_for_reviews = models.BooleanField(
        default=True,
        help_text="Whether accepting new prescription reviews"
    )
    working_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Start time of working hours"
    )
    working_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text="End time of working hours"
    )
    working_days = models.CharField(
        max_length=100,
        default='Mon,Tue,Wed,Thu,Fri',
        help_text="Comma-separated days, e.g., 'Mon,Tue,Wed'"
    )

    # Performance Tracking
    total_reviews_completed = models.PositiveIntegerField(
        default=0,
        help_text="Total prescription reviews completed"
    )
    total_approved = models.PositiveIntegerField(
        default=0,
        help_text="Total prescriptions approved by pharmacist"
    )
    total_escalated = models.PositiveIntegerField(
        default=0,
        help_text="Total prescriptions escalated to physician"
    )
    total_rejected = models.PositiveIntegerField(
        default=0,
        help_text="Total prescription requests rejected"
    )
    average_review_time_minutes = models.FloatField(
        default=0.0,
        help_text="Average time to review prescription request (minutes)"
    )
    clinical_interventions_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of clinical interventions made (drug interactions, dosage corrections, etc.)"
    )

    # Additional Professional Info
    clinical_interests = models.TextField(
        null=True,
        blank=True,
        help_text="Areas of clinical pharmacy interest"
    )
    languages_spoken = models.CharField(
        max_length=200,
        help_text="Comma-separated languages",
        null=True,
        blank=True
    )
    pharmacy_school = models.CharField(
        max_length=200,
        help_text="Pharmacy school attended",
        null=True,
        blank=True
    )
    graduation_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Year of pharmacy school graduation"
    )

    # Contact and Settings
    professional_email = models.EmailField(
        null=True,
        blank=True,
        help_text="Professional email for prescription notifications"
    )
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Professional phone number"
    )
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Notification preferences for prescription reviews"
    )

    class Meta:
        db_table = 'pharmacists'
        verbose_name = 'Pharmacist'
        verbose_name_plural = 'Pharmacists'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hospital', 'is_active'], name='idx_pharmacist_hospital_active'),
            models.Index(fields=['triage_specialty', 'auto_assign_triage'], name='idx_pharmacist_triage'),
            models.Index(fields=['status', 'available_for_reviews'], name='idx_pharmacist_availability'),
            models.Index(fields=['prescribing_authority_level'], name='idx_pharmacist_authority'),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_triage_specialty_display()}"

    def clean(self):
        """Validate pharmacist data"""
        super().clean()

        # Validate license expiry
        if self.license_expiry_date and self.license_expiry_date < timezone.now().date():
            raise ValidationError("Pharmacy license has expired. Please renew before continuing practice.")

        # Validate controlled substance authority requires base prescribing authority
        if self.can_prescribe_controlled and self.prescribing_authority_level == 'none':
            raise ValidationError(
                "Cannot prescribe controlled substances without basic prescribing authority. "
                "Please set prescribing_authority_level to 'supplementary' or 'independent'."
            )

        # Validate CPA requires supervising physician
        if self.collaborative_practice_agreement and not self.supervising_physician:
            raise ValidationError(
                "Collaborative Practice Agreement requires a supervising physician to be assigned."
            )

        # Validate working hours
        if self.working_hours_start and self.working_hours_end:
            if self.working_hours_start >= self.working_hours_end:
                raise ValidationError("Working hours start time must be before end time.")

    def save(self, *args, **kwargs):
        """Custom save with validation"""
        self.clean()
        super().save(*args, **kwargs)

    def get_full_name(self):
        """Get pharmacist's full name"""
        return self.user.get_full_name()

    def is_license_valid(self):
        """
        Check if pharmacist's license is currently valid.

        Returns:
            bool: True if license is valid (not expired and pharmacist is active)
        """
        if not self.is_active or self.status != 'active':
            return False

        if not self.pharmacy_license_number:
            return False

        if self.license_expiry_date and self.license_expiry_date < timezone.now().date():
            return False

        return True

    def can_access_prescriptions(self):
        """
        Check if pharmacist can access patient prescriptions.
        Implements PCN (Pharmacists Council of Nigeria) verification.

        Returns:
            dict: {'allowed': bool, 'reason': str}
        """
        # Must have valid license
        if not self.is_license_valid():
            return {
                'allowed': False,
                'reason': 'Pharmacy license is expired or invalid. Please renew your license.'
            }

        # Must be able to review prescriptions
        if not self.can_review_prescriptions:
            return {
                'allowed': False,
                'reason': 'Your account does not have prescription review permissions.'
            }

        # Must be available for reviews
        if not self.available_for_reviews:
            return {
                'allowed': False,
                'reason': 'Your account is currently not available for prescription reviews.'
            }

        return {
            'allowed': True,
            'reason': 'Access granted'
        }

    def get_approval_rate(self):
        """Calculate approval rate (approved / total reviewed)"""
        if self.total_reviews_completed == 0:
            return 0.0
        return (self.total_approved / self.total_reviews_completed) * 100

    def get_escalation_rate(self):
        """Calculate escalation rate (escalated / total reviewed)"""
        if self.total_reviews_completed == 0:
            return 0.0
        return (self.total_escalated / self.total_reviews_completed) * 100

    def get_intervention_rate(self):
        """Calculate clinical intervention rate"""
        if self.total_reviews_completed == 0:
            return 0.0
        return (self.clinical_interventions_count / self.total_reviews_completed) * 100

    def can_prescribe_medication(self, medication_type='standard'):
        """
        Check if pharmacist can prescribe specific medication type

        Args:
            medication_type (str): 'standard', 'controlled', or specific drug class

        Returns:
            bool: Whether pharmacist can prescribe this medication
        """
        # Must have active license and be available
        if not self.is_active or self.status != 'active':
            return False

        # Must have some prescribing authority
        if self.prescribing_authority_level == 'none':
            return False

        # Check controlled substances
        if medication_type == 'controlled':
            return self.can_prescribe_controlled

        # Standard medications require at least supplementary authority
        if medication_type == 'standard':
            return self.prescribing_authority_level in ['supplementary', 'independent', 'community']

        return True

    def is_available_now(self):
        """Check if pharmacist is available for reviews right now"""
        if not self.is_active or self.status != 'active' or not self.available_for_reviews:
            return False

        # Check working days
        current_day = timezone.now().strftime('%a')
        if self.working_days and current_day not in self.working_days:
            return False

        # Check working hours
        if self.working_hours_start and self.working_hours_end:
            current_time = timezone.now().time()
            if not (self.working_hours_start <= current_time <= self.working_hours_end):
                return False

        return True

    def increment_review_stats(self, action='approved', review_time_minutes=None, had_intervention=False):
        """
        Increment review statistics

        Args:
            action (str): 'approved', 'escalated', or 'rejected'
            review_time_minutes (float, optional): Time taken to review
            had_intervention (bool): Whether clinical intervention was made
        """
        self.total_reviews_completed += 1

        if action == 'approved':
            self.total_approved += 1
        elif action == 'escalated':
            self.total_escalated += 1
        elif action == 'rejected':
            self.total_rejected += 1

        if had_intervention:
            self.clinical_interventions_count += 1

        # Update average review time
        if review_time_minutes is not None:
            total_time = self.average_review_time_minutes * (self.total_reviews_completed - 1)
            self.average_review_time_minutes = (total_time + review_time_minutes) / self.total_reviews_completed

        self.save(update_fields=[
            'total_reviews_completed', 'total_approved', 'total_escalated',
            'total_rejected', 'clinical_interventions_count', 'average_review_time_minutes'
        ])
