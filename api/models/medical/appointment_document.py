from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import os

class AppointmentDocument(models.Model):
    """
    Model to manage documents related to appointments
    """
    DOCUMENT_TYPE_CHOICES = [
        ('prescription', 'Prescription'),
        ('lab_report', 'Laboratory Report'),
        ('medical_certificate', 'Medical Certificate'),
        ('referral_letter', 'Referral Letter'),
        ('consent_form', 'Consent Form'),
        ('insurance_claim', 'Insurance Claim'),
        ('medical_history', 'Medical History'),
        ('test_result', 'Test Result'),
        ('x_ray', 'X-Ray'),
        ('scan', 'Scan'),
        ('other', 'Other'),
    ]

    # Basic Information
    appointment = models.ForeignKey(
        'api.Appointment',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPE_CHOICES
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # File Information
    file = models.FileField(
        upload_to='appointment_documents/%Y/%m/%d/',
        help_text="Upload document file"
    )
    file_size = models.PositiveIntegerField(
        help_text="File size in bytes",
        editable=False
    )
    file_type = models.CharField(
        max_length=50,
        help_text="MIME type of the file",
        editable=False
    )
    
    # Document Metadata
    issued_by = models.ForeignKey(
        'api.Doctor',
        on_delete=models.PROTECT,
        related_name='issued_documents'
    )
    issued_date = models.DateTimeField(default=timezone.now)
    valid_until = models.DateField(
        null=True,
        blank=True,
        help_text="Document validity end date"
    )
    
    # Document Status
    is_confidential = models.BooleanField(
        default=False,
        help_text="Mark document as confidential"
    )
    requires_signature = models.BooleanField(
        default=False,
        help_text="Document requires patient signature"
    )
    is_signed = models.BooleanField(
        default=False,
        help_text="Document has been signed"
    )
    signed_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='signed_documents'
    )
    signed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Version Control
    version = models.PositiveIntegerField(
        default=1,
        help_text="Document version number"
    )
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_version'
    )
    
    # Access Control
    allowed_viewers = models.ManyToManyField(
        'api.CustomUser',
        blank=True,
        related_name='accessible_documents',
        help_text="Users allowed to view this document"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_type']),
            models.Index(fields=['issued_date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_document_type_display()}"

    def clean(self):
        """Validate document"""
        if self.requires_signature and self.is_signed and not self.signed_by:
            raise ValidationError("Signed document must have a signer")
            
        if self.signed_by and not self.is_signed:
            raise ValidationError("Document with signer must be marked as signed")
            
        if self.valid_until and self.valid_until < timezone.now().date():
            raise ValidationError("Validity end date must be in the future")
            
        if self.previous_version and self.version <= self.previous_version.version:
            raise ValidationError("Version number must be greater than previous version")

    def save(self, *args, **kwargs):
        # Set file metadata
        if self.file:
            self.file_size = self.file.size
            self.file_type = self._get_file_type()
            
        # Set signed_at timestamp
        if self.is_signed and self.signed_by and not self.signed_at:
            self.signed_at = timezone.now()
            
        self.clean()
        super().save(*args, **kwargs)

    def _get_file_type(self):
        """Get MIME type of the file"""
        name = self.file.name
        _, extension = os.path.splitext(name)
        return {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.txt': 'text/plain'
        }.get(extension.lower(), 'application/octet-stream')

    def sign_document(self, user):
        """Sign the document"""
        if not self.requires_signature:
            raise ValidationError("This document does not require signature")
            
        if self.is_signed:
            raise ValidationError("Document is already signed")
            
        self.is_signed = True
        self.signed_by = user
        self.signed_at = timezone.now()
        self.save()

    def create_new_version(self, file, title=None, description=None):
        """Create a new version of the document"""
        new_version = AppointmentDocument.objects.create(
            appointment=self.appointment,
            document_type=self.document_type,
            title=title or self.title,
            description=description or self.description,
            file=file,
            issued_by=self.issued_by,
            is_confidential=self.is_confidential,
            requires_signature=self.requires_signature,
            version=self.version + 1,
            previous_version=self
        )
        return new_version

    def get_all_versions(self):
        """Get all versions of the document"""
        versions = []
        current = self
        
        # Get previous versions
        while current.previous_version:
            versions.append(current.previous_version)
            current = current.previous_version
            
        # Get next versions
        current = self
        while hasattr(current, 'next_version') and current.next_version:
            versions.append(current.next_version.first())
            current = current.next_version.first()
            
        return sorted(versions, key=lambda x: x.version)

    @property
    def is_valid(self):
        """Check if document is still valid"""
        if not self.valid_until:
            return True
        return self.valid_until >= timezone.now().date()

    @property
    def requires_action(self):
        """Check if document requires any action"""
        return (
            (self.requires_signature and not self.is_signed) or
            (self.valid_until and not self.is_valid)
        )

    def get_document_summary(self):
        """Get summary of document details"""
        return {
            'title': self.title,
            'type': self.get_document_type_display(),
            'issued_by': f"Dr. {self.issued_by.user.get_full_name()}",
            'issued_date': self.issued_date,
            'version': self.version,
            'is_signed': self.is_signed,
            'is_valid': self.is_valid,
            'file_type': self.file_type,
            'file_size': self.file_size,
        } 