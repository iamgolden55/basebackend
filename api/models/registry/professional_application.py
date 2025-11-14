"""
Professional Application Models

Models for managing professional registration applications to PHB National Registry.
Based on NHS GMC registration model - handles licensing and credentialing.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid
from ..base import TimestampedModel

User = get_user_model()


class ProfessionalApplication(TimestampedModel):
    """
    Application to PHB National Registry (similar to GMC registration).

    This is Step 1-4 of the NHS registration process:
    1. Online application submission
    2. Document upload and verification
    3. Credential verification
    4. License issuance

    This is SEPARATE from hospital employment (credentialing).
    """

    APPLICATION_STATUS = [
        ('draft', 'Draft - Incomplete'),
        ('submitted', 'Submitted - Pending Review'),
        ('under_review', 'Under Review'),
        ('documents_requested', 'Additional Documents Requested'),
        ('payment_pending', 'Payment Pending'),
        ('payment_confirmed', 'Payment Confirmed'),
        ('verification_in_progress', 'Verification In Progress'),
        ('approved', 'Approved - License Issued'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
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

    SPECIALIZATION_CHOICES = [
        # Doctors
        ('general_practice', 'General Practice'),
        ('internal_medicine', 'Internal Medicine'),
        ('surgery', 'Surgery'),
        ('pediatrics', 'Pediatrics'),
        ('obstetrics_gynecology', 'Obstetrics & Gynecology'),
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('psychiatry', 'Psychiatry'),
        ('oncology', 'Oncology'),
        ('emergency_medicine', 'Emergency Medicine'),
        ('radiology', 'Radiology'),
        ('anesthesiology', 'Anesthesiology'),

        # Pharmacists
        ('community_pharmacy', 'Community Pharmacy'),
        ('hospital_pharmacy', 'Hospital Pharmacy'),
        ('clinical_pharmacy', 'Clinical Pharmacy'),
        ('oncology_pharmacy', 'Oncology Pharmacy'),
        ('pediatric_pharmacy', 'Pediatric Pharmacy'),

        # Nurses
        ('general_nursing', 'General Nursing'),
        ('critical_care_nursing', 'Critical Care Nursing'),
        ('pediatric_nursing', 'Pediatric Nursing'),
        ('psychiatric_nursing', 'Psychiatric Nursing'),
        ('oncology_nursing', 'Oncology Nursing'),

        # Other
        ('other', 'Other (Specify in Notes)'),
    ]

    # Identification
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the application'
    )
    application_reference = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text='Human-readable reference (e.g., PHB-APP-2025-00123)'
    )

    # Applicant Information
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='professional_applications',
        help_text='User account submitting the application'
    )
    professional_type = models.CharField(
        max_length=30,
        choices=PROFESSIONAL_TYPE,
        db_index=True,
        help_text='Type of professional applying (doctor, pharmacist, etc.)'
    )

    # Personal Details
    title = models.CharField(
        max_length=10,
        choices=[
            ('Dr', 'Dr.'),
            ('Mr', 'Mr.'),
            ('Mrs', 'Mrs.'),
            ('Ms', 'Ms.'),
            ('Prof', 'Prof.'),
        ],
        help_text='Professional title'
    )
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(help_text='Date of birth')
    gender = models.CharField(
        max_length=20,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
            ('prefer_not_to_say', 'Prefer not to say'),
        ]
    )
    nationality = models.CharField(
        max_length=100,
        help_text='Nationality (e.g., Nigerian, British, etc.)'
    )

    # Contact Information
    email = models.EmailField(help_text='Primary email address')
    phone = models.CharField(max_length=20, help_text='Primary phone number')
    alternate_phone = models.CharField(max_length=20, blank=True)

    # Address
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postcode = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default='Nigeria')

    # Professional Qualifications
    primary_qualification = models.CharField(
        max_length=255,
        help_text='Primary degree (e.g., MBBS, BPharm, etc.)'
    )
    qualification_institution = models.CharField(
        max_length=255,
        help_text='Institution where primary qualification was obtained'
    )
    qualification_year = models.PositiveIntegerField(
        help_text='Year of qualification'
    )
    qualification_country = models.CharField(
        max_length=100,
        help_text='Country of qualification'
    )

    # Additional Qualifications (JSON array)
    additional_qualifications = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of additional qualifications [{degree, institution, year}, ...]'
    )

    # Specialization
    specialization = models.CharField(
        max_length=50,
        choices=SPECIALIZATION_CHOICES,
        help_text='Area of specialization'
    )
    subspecialization = models.CharField(
        max_length=100,
        blank=True,
        help_text='Sub-specialization if applicable'
    )

    # Professional Registration (from home country/other jurisdictions)
    home_registration_body = models.CharField(
        max_length=255,
        blank=True,
        help_text='Registration body in home country (e.g., GMC, MDCN, etc.)'
    )
    home_registration_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Registration number with home registration body'
    )
    home_registration_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date of home registration'
    )

    # Employment History (JSON array)
    employment_history = models.JSONField(
        default=list,
        blank=True,
        help_text='Previous employment [{employer, position, from_date, to_date, responsibilities}, ...]'
    )

    # Years of Experience
    years_of_experience = models.PositiveIntegerField(
        default=0,
        help_text='Total years of professional experience'
    )

    # Application Status
    status = models.CharField(
        max_length=30,
        choices=APPLICATION_STATUS,
        default='draft',
        db_index=True,
        help_text='Current status of the application'
    )

    # Dates
    submitted_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the application was submitted'
    )
    under_review_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When review started'
    )
    decision_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When decision was made (approved/rejected)'
    )

    # Review Information
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications',
        help_text='Admin user who reviewed the application'
    )
    review_notes = models.TextField(
        blank=True,
        help_text='Internal review notes from admin'
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text='Reason for rejection (if rejected)'
    )

    # Payment Information
    application_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Application fee amount (e.g., ₦50,000)'
    )
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text='Paystack payment reference'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ],
        default='pending'
    )
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When payment was confirmed'
    )

    # License Information (populated after approval)
    phb_license_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text='PHB professional license number (e.g., PHB-DOC-2025-00123)'
    )
    license_issue_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date license was issued'
    )
    license_expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text='License expiry date (typically 1 year from issue)'
    )

    # Document Verification Status
    documents_verified = models.BooleanField(
        default=False,
        help_text='Whether all required documents have been verified'
    )
    identity_verified = models.BooleanField(
        default=False,
        help_text='Whether identity has been verified'
    )
    qualifications_verified = models.BooleanField(
        default=False,
        help_text='Whether qualifications have been verified'
    )
    registration_verified = models.BooleanField(
        default=False,
        help_text='Whether professional registration has been verified'
    )

    # Additional Information
    reason_for_application = models.TextField(
        blank=True,
        help_text='Why applying for PHB registration'
    )
    practice_intentions = models.TextField(
        blank=True,
        help_text='Intended practice settings (hospital, private, both, etc.)'
    )
    languages_spoken = models.CharField(
        max_length=255,
        blank=True,
        help_text='Languages spoken (comma-separated)'
    )

    # Terms and Conditions
    agreed_to_terms = models.BooleanField(
        default=False,
        help_text='Applicant agreed to terms and conditions'
    )
    agreed_to_code_of_conduct = models.BooleanField(
        default=False,
        help_text='Applicant agreed to professional code of conduct'
    )
    declaration_truthful = models.BooleanField(
        default=False,
        help_text='Applicant declared all information is truthful'
    )

    # Document Rejection Status (for UI flagging)
    has_rejected_documents = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Flag indicating application has one or more rejected documents that need resubmission'
    )

    class Meta:
        db_table = 'professional_applications'
        ordering = ['-submitted_date', '-created_at']
        indexes = [
            models.Index(fields=['status', '-submitted_date'], name='idx_app_status_date'),
            models.Index(fields=['professional_type', 'status'], name='idx_app_type_status'),
            models.Index(fields=['user', '-created_at'], name='idx_app_user_date'),
            models.Index(fields=['phb_license_number'], name='idx_app_license'),
            models.Index(fields=['application_reference'], name='idx_app_ref'),
        ]
        verbose_name = 'Professional Application'
        verbose_name_plural = 'Professional Applications'

    def __str__(self):
        return f"{self.application_reference} - {self.get_full_name()} ({self.get_professional_type_display()})"

    def get_full_name(self):
        """Get applicant's full name"""
        parts = [self.title, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return ' '.join(parts)

    @property
    def is_draft(self):
        """Check if application is still in draft"""
        return self.status == 'draft'

    @property
    def is_submitted(self):
        """Check if application has been submitted"""
        return self.status not in ['draft']

    @property
    def is_approved(self):
        """Check if application has been approved"""
        return self.status == 'approved'

    @property
    def is_pending_review(self):
        """Check if application is pending review"""
        return self.status in ['submitted', 'under_review', 'documents_requested', 'verification_in_progress']

    @property
    def requires_payment(self):
        """Check if payment is required"""
        return self.payment_status != 'paid' and self.application_fee > 0

    @property
    def all_documents_verified(self):
        """Check if all verification checks are complete"""
        return (
            self.documents_verified and
            self.identity_verified and
            self.qualifications_verified and
            self.registration_verified
        )

    def submit_application(self):
        """Submit the application for review"""
        if self.status != 'draft':
            raise ValueError('Only draft applications can be submitted')

        self.status = 'submitted'
        self.submitted_date = timezone.now()
        self.save(update_fields=['status', 'submitted_date', 'updated_at'])

    def start_review(self, reviewer):
        """Start reviewing the application"""
        self.status = 'under_review'
        self.under_review_date = timezone.now()
        self.reviewed_by = reviewer
        self.save(update_fields=['status', 'under_review_date', 'reviewed_by', 'updated_at'])

    def approve_application(self, license_number, reviewer, review_notes=''):
        """Approve the application and issue license"""
        self.status = 'approved'
        self.decision_date = timezone.now()
        self.reviewed_by = reviewer
        self.review_notes = review_notes
        self.phb_license_number = license_number
        self.license_issue_date = timezone.now().date()
        # License expires after 1 year
        from datetime import timedelta
        self.license_expiry_date = (timezone.now() + timedelta(days=365)).date()

        self.save(update_fields=[
            'status', 'decision_date', 'reviewed_by', 'review_notes',
            'phb_license_number', 'license_issue_date', 'license_expiry_date',
            'updated_at'
        ])

    def reject_application(self, reviewer, rejection_reason):
        """Reject the application"""
        self.status = 'rejected'
        self.decision_date = timezone.now()
        self.reviewed_by = reviewer
        self.rejection_reason = rejection_reason
        self.save(update_fields=[
            'status', 'decision_date', 'reviewed_by', 'rejection_reason', 'updated_at'
        ])

    def request_additional_documents(self, reviewer, notes):
        """Request additional documents from applicant"""
        self.status = 'documents_requested'
        self.reviewed_by = reviewer
        self.review_notes = notes
        self.save(update_fields=['status', 'reviewed_by', 'review_notes', 'updated_at'])

    def confirm_payment(self, payment_reference):
        """Confirm payment has been received"""
        self.payment_status = 'paid'
        self.payment_reference = payment_reference
        self.payment_date = timezone.now()
        self.save(update_fields=['payment_status', 'payment_reference', 'payment_date', 'updated_at'])
