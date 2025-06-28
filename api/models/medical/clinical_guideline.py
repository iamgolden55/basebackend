# api/models/medical/clinical_guideline.py

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class ClinicalGuideline(models.Model):
    """
    Clinical Guidelines Model for hospitals to manage medical protocols and procedures.
    This model allows hospital administrators to upload, manage, and publish clinical guidelines
    for their medical staff to access and follow.
    """
    
    # Core identification
    guideline_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    title = models.CharField(max_length=300, help_text="Title of the clinical guideline")
    description = models.TextField(help_text="Detailed description of the guideline")
    version = models.CharField(max_length=20, default="1.0", help_text="Version number of the guideline")
    
    # Organization ownership
    organization = models.ForeignKey(
        'Hospital', 
        on_delete=models.CASCADE, 
        related_name='clinical_guidelines',
        help_text="Hospital that owns this guideline"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_guidelines',
        help_text="Hospital admin who created this guideline"
    )
    
    # Categorization
    CATEGORY_CHOICES = [
        ('emergency', 'Emergency Protocols'),
        ('surgery', 'Surgical Procedures'),
        ('medication', 'Medication Guidelines'),
        ('diagnosis', 'Diagnostic Protocols'),
        ('treatment', 'Treatment Plans'),
        ('prevention', 'Preventive Care'),
        ('infection_control', 'Infection Control'),
        ('patient_safety', 'Patient Safety'),
        ('quality_assurance', 'Quality Assurance'),
        ('maternity', 'Maternity Care'),
        ('pediatric', 'Pediatric Care'),
        ('geriatric', 'Geriatric Care'),
        ('mental_health', 'Mental Health'),
        ('oncology', 'Oncology'),
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('orthopedics', 'Orthopedics'),
        ('radiology', 'Radiology'),
        ('laboratory', 'Laboratory Procedures'),
        ('nursing', 'Nursing Protocols'),
        ('other', 'Other')
    ]
    category = models.CharField(
        max_length=30, 
        choices=CATEGORY_CHOICES,
        help_text="Category of the clinical guideline"
    )
    specialty = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Medical specialty this guideline applies to"
    )
    keywords = models.JSONField(
        default=list, 
        help_text="Search keywords for this guideline"
    )
    
    # Content
    CONTENT_TYPE_CHOICES = [
        ('pdf', 'PDF Document'),
        ('text', 'Text Content'),
        ('mixed', 'Mixed Content')
    ]
    content_type = models.CharField(
        max_length=20, 
        choices=CONTENT_TYPE_CHOICES,
        default='pdf'
    )
    text_content = models.TextField(
        blank=True, 
        null=True,
        help_text="Text content of the guideline"
    )
    file_path = models.CharField(
        max_length=500,
        blank=True, 
        null=True,
        help_text="Path to uploaded guideline file"
    )
    
    # Publication & validity
    effective_date = models.DateField(
        help_text="Date when this guideline becomes effective"
    )
    expiry_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date when this guideline expires (optional)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this guideline is currently active"
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Whether this guideline is published and visible to staff"
    )
    
    # Approval workflow
    APPROVAL_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived')
    ]
    approval_status = models.CharField(
        max_length=20, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='draft'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_guidelines',
        help_text="Administrator who approved this guideline"
    )
    approved_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date and time when this guideline was approved"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    access_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this guideline has been accessed"
    )
    
    # Target audience
    target_roles = models.JSONField(
        default=list,
        help_text="List of roles this guideline is intended for (e.g., ['doctor', 'nurse'])"
    )
    
    # Priority level
    PRIORITY_CHOICES = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('critical', 'Critical')
    ]
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Priority level of this guideline"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['category', 'specialty']),
            models.Index(fields=['approval_status', 'is_published']),
            models.Index(fields=['effective_date', 'expiry_date']),
            models.Index(fields=['created_at']),
            models.Index(fields=['guideline_id']),
        ]
        
    def __str__(self):
        return f"{self.title} - {self.organization.name} (v{self.version})"
    
    @property
    def is_expired(self):
        """Check if the guideline has expired"""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False
    
    @property
    def is_effective(self):
        """Check if the guideline is currently effective"""
        return timezone.now().date() >= self.effective_date
    
    @property
    def is_accessible(self):
        """Check if the guideline is accessible to staff"""
        return (self.is_active and 
                self.is_published and 
                self.approval_status == 'approved' and
                self.is_effective and
                not self.is_expired)
    
    def increment_access_count(self):
        """Increment the access count for this guideline"""
        self.access_count += 1
        self.save(update_fields=['access_count'])
    
    def approve(self, approved_by_user):
        """Approve this guideline"""
        self.approval_status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save(update_fields=['approval_status', 'approved_by', 'approved_at'])
    
    def publish(self):
        """Publish this guideline (make it visible to staff)"""
        if self.approval_status == 'approved':
            self.is_published = True
            self.save(update_fields=['is_published'])
            return True
        return False
    
    def archive(self):
        """Archive this guideline"""
        self.approval_status = 'archived'
        self.is_active = False
        self.is_published = False
        self.save(update_fields=['approval_status', 'is_active', 'is_published'])


class GuidelineAccess(models.Model):
    """
    Model to track access to clinical guidelines for audit purposes.
    This helps hospitals monitor which guidelines are being accessed and by whom.
    """
    
    # Core relationships
    guideline = models.ForeignKey(
        ClinicalGuideline, 
        on_delete=models.CASCADE, 
        related_name='access_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        help_text="User who accessed the guideline"
    )
    
    # Access details
    accessed_at = models.DateTimeField(auto_now_add=True)
    
    ACTION_CHOICES = [
        ('view', 'Viewed'),
        ('download', 'Downloaded'),
        ('shared', 'Shared'),
        ('printed', 'Printed'),
        ('bookmarked', 'Bookmarked')
    ]
    action = models.CharField(
        max_length=20, 
        choices=ACTION_CHOICES,
        help_text="Type of access action performed"
    )
    
    # Technical details
    ip_address = models.GenericIPAddressField(
        help_text="IP address from which the access occurred"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Browser/client information"
    )
    
    # Session information
    session_duration = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Duration of access session in seconds"
    )
    
    # Additional context
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="Department from which access occurred"
    )
    device_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of device used (mobile, desktop, tablet)"
    )
    
    class Meta:
        ordering = ['-accessed_at']
        indexes = [
            models.Index(fields=['guideline', 'accessed_at']),
            models.Index(fields=['user', 'accessed_at']),
            models.Index(fields=['action', 'accessed_at']),
            models.Index(fields=['guideline', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.email} {self.action} {self.guideline.title} at {self.accessed_at}"


class GuidelineBookmark(models.Model):
    """
    Model to allow medical staff to bookmark clinical guidelines for quick access.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='guideline_bookmarks'
    )
    guideline = models.ForeignKey(
        ClinicalGuideline,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    
    # Bookmark details
    bookmarked_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(
        blank=True,
        help_text="Personal notes about this guideline"
    )
    
    # Organization check
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'guideline')
        ordering = ['-bookmarked_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['guideline', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} bookmarked {self.guideline.title}"