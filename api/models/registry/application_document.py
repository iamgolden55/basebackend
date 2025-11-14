"""
Application Document Models

Models for managing document uploads for professional applications.
Handles verification of credentials, identity, and qualifications.
"""

from django.db import models
from django.utils import timezone
import uuid
from ..base import TimestampedModel


class ApplicationDocument(TimestampedModel):
    """
    Documents uploaded as part of professional application.

    Required documents (NHS GMC model):
    1. Identity proof (passport, national ID)
    2. Professional qualification certificates
    3. Transcripts/academic records
    4. Professional registration certificate (from home country)
    5. CV/Resume
    6. Passport photographs
    7. Character references
    8. Proof of address
    """

    DOCUMENT_TYPE = [
        # Identity Documents
        ('passport', 'Passport'),
        ('national_id', 'National ID Card'),
        ('drivers_license', 'Driver\'s License'),

        # Professional Credentials
        ('primary_degree_certificate', 'Primary Degree Certificate'),
        ('postgraduate_certificate', 'Postgraduate Certificate'),
        ('fellowship_certificate', 'Fellowship Certificate'),
        ('transcript', 'Academic Transcript'),

        # Registration Documents
        ('home_registration_certificate', 'Home Country Registration Certificate'),
        ('practicing_license', 'Current Practicing License'),
        ('good_standing_certificate', 'Certificate of Good Standing'),

        # Supporting Documents
        ('cv_resume', 'CV/Resume'),
        ('passport_photo', 'Passport Photograph'),
        ('proof_of_address', 'Proof of Address'),
        ('character_reference', 'Character Reference Letter'),
        ('employment_letter', 'Employment Verification Letter'),
        ('internship_certificate', 'Internship/House Job Certificate'),

        # Specialized
        ('specialty_certificate', 'Specialty Board Certification'),
        ('malpractice_insurance', 'Malpractice Insurance Certificate'),
        ('criminal_record_check', 'Criminal Record Check'),

        # Other
        ('other', 'Other Document'),
    ]

    VERIFICATION_STATUS = [
        ('pending', 'Pending Verification'),
        ('under_review', 'Under Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected - Invalid'),
        ('clarification_needed', 'Clarification Needed'),
    ]

    # Identification
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the document'
    )

    # Link to Application
    application = models.ForeignKey(
        'ProfessionalApplication',
        on_delete=models.CASCADE,
        related_name='documents',
        help_text='Professional application this document belongs to'
    )

    # Document Information
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPE,
        db_index=True,
        help_text='Type of document'
    )
    document_title = models.CharField(
        max_length=255,
        help_text='Title/name of the document'
    )
    description = models.TextField(
        blank=True,
        help_text='Optional description or notes about the document'
    )

    # File Upload
    file = models.FileField(
        upload_to='professional_applications/%Y/%m/',
        help_text='Uploaded document file (PDF, JPG, PNG)'
    )
    file_size = models.PositiveIntegerField(
        help_text='File size in bytes',
        null=True,
        blank=True
    )
    file_type = models.CharField(
        max_length=50,
        help_text='MIME type of the file',
        blank=True
    )
    original_filename = models.CharField(
        max_length=255,
        help_text='Original filename when uploaded',
        blank=True
    )

    # Verification
    verification_status = models.CharField(
        max_length=30,
        choices=VERIFICATION_STATUS,
        default='pending',
        db_index=True,
        help_text='Verification status of the document'
    )
    verified_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents',
        help_text='Admin user who verified the document'
    )
    verified_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the document was verified'
    )
    verification_notes = models.TextField(
        blank=True,
        help_text='Notes from the verifier'
    )

    # Document Details (for credential verification)
    issue_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date document was issued (if applicable)'
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text='Expiry date (if applicable, e.g., for licenses)'
    )
    issuing_authority = models.CharField(
        max_length=255,
        blank=True,
        help_text='Organization that issued the document (e.g., university, GMC, etc.)'
    )
    document_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Document/certificate number (if applicable)'
    )

    # Metadata
    is_required = models.BooleanField(
        default=True,
        help_text='Whether this document is required for application approval'
    )
    uploaded_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='uploaded_documents',
        help_text='User who uploaded the document'
    )

    # Rejection Tracking & Re-upload Controls
    rejection_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of times this document has been rejected'
    )
    max_rejection_attempts = models.PositiveIntegerField(
        default=3,
        help_text='Maximum number of times this document can be rejected before requiring admin intervention'
    )
    resubmission_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Deadline for re-uploading a rejected document (typically 7 days from rejection)'
    )
    locked_after_verification = models.BooleanField(
        default=False,
        help_text='Whether this document is locked and cannot be modified after verification (prevents changes during re-upload of other docs)'
    )

    class Meta:
        db_table = 'application_documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['application', 'document_type'], name='idx_doc_app_type'),
            models.Index(fields=['verification_status', '-created_at'], name='idx_doc_status'),
            models.Index(fields=['application', 'verification_status'], name='idx_doc_app_status'),
        ]
        verbose_name = 'Application Document'
        verbose_name_plural = 'Application Documents'

    def __str__(self):
        return f"{self.document_title} ({self.get_document_type_display()}) - {self.application.application_reference}"

    @property
    def is_verified(self):
        """Check if document has been verified"""
        return self.verification_status == 'verified'

    @property
    def is_pending(self):
        """Check if document is pending verification"""
        return self.verification_status == 'pending'

    @property
    def is_expired(self):
        """Check if document has expired"""
        if not self.expiry_date:
            return False
        from datetime import date
        return self.expiry_date < date.today()

    @property
    def can_be_replaced(self):
        """Check if document can be replaced/re-uploaded"""
        # Can replace if:
        # 1. Document is rejected AND
        # 2. Haven't exceeded max rejection attempts AND
        # 3. Within resubmission deadline (if set) AND
        # 4. Not locked after verification
        if self.verification_status != 'rejected':
            return False

        if self.rejection_count >= self.max_rejection_attempts:
            return False

        if self.resubmission_deadline and timezone.now() > self.resubmission_deadline:
            return False

        if self.locked_after_verification:
            return False

        return True

    @property
    def attempts_remaining(self):
        """Get number of rejection attempts remaining"""
        return max(0, self.max_rejection_attempts - self.rejection_count)

    @property
    def is_deadline_approaching(self):
        """Check if resubmission deadline is approaching (within 2 days)"""
        if not self.resubmission_deadline:
            return False
        from datetime import timedelta
        return timezone.now() + timedelta(days=2) >= self.resubmission_deadline

    def verify_document(self, verifier, notes=''):
        """Mark document as verified and lock it"""
        self.verification_status = 'verified'
        self.verified_by = verifier
        self.verified_date = timezone.now()
        self.verification_notes = notes
        self.locked_after_verification = True  # Lock verified documents
        self.save(update_fields=[
            'verification_status', 'verified_by', 'verified_date',
            'verification_notes', 'locked_after_verification', 'updated_at'
        ])

    def reject_document(self, verifier, reason):
        """Reject document as invalid and set resubmission deadline"""
        from datetime import timedelta

        self.verification_status = 'rejected'
        self.verified_by = verifier
        self.verified_date = timezone.now()
        self.verification_notes = reason
        self.rejection_count += 1  # Increment rejection counter

        # Set resubmission deadline (7 days from now)
        self.resubmission_deadline = timezone.now() + timedelta(days=7)

        self.save(update_fields=[
            'verification_status', 'verified_by', 'verified_date',
            'verification_notes', 'rejection_count', 'resubmission_deadline', 'updated_at'
        ])

    def request_clarification(self, verifier, clarification_needed):
        """Request clarification or additional information"""
        self.verification_status = 'clarification_needed'
        self.verified_by = verifier
        self.verification_notes = clarification_needed
        self.save(update_fields=[
            'verification_status', 'verified_by', 'verification_notes', 'updated_at'
        ])


def get_required_documents_for_profession(professional_type):
    """
    Get list of required documents for a specific professional type.

    Based on NHS GMC requirements and standard credentialing processes.
    """
    # Base documents required for all professionals
    base_required = [
        'passport',  # or national_id
        'primary_degree_certificate',
        'transcript',
        'cv_resume',
        'passport_photo',
        'proof_of_address',
    ]

    # Profession-specific additional requirements
    profession_specific = {
        'doctor': [
            'home_registration_certificate',  # e.g., GMC, MDCN
            'good_standing_certificate',
            'internship_certificate',
            'character_reference',
        ],
        'pharmacist': [
            'home_registration_certificate',  # e.g., PCN
            'good_standing_certificate',
            'internship_certificate',
        ],
        'nurse': [
            'home_registration_certificate',
            'practicing_license',
            'character_reference',
        ],
        'physiotherapist': [
            'home_registration_certificate',
            'practicing_license',
        ],
        'dentist': [
            'home_registration_certificate',
            'good_standing_certificate',
            'internship_certificate',
        ],
    }

    # Combine base and profession-specific
    required = base_required.copy()
    if professional_type in profession_specific:
        required.extend(profession_specific[professional_type])

    return required
