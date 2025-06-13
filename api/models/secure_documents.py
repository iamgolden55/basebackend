"""
🛡️ MEDICAL VAULT 3.0 - SECURE DOCUMENT MODELS
User-Specific File Ownership System
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import os

class SecureDocument(models.Model):
    """🗃️ Secure Document Model with User Ownership"""
    
    # Core identification
    file_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='secure_documents')
    
    # File information
    original_filename = models.CharField(max_length=255)
    secure_filename = models.CharField(max_length=255, unique=True)
    file_extension = models.CharField(max_length=10)
    file_type = models.CharField(max_length=20)  # 'image', 'document', 'other'
    file_size = models.PositiveIntegerField()  # Size in bytes
    
    # Security information
    encryption_key_id = models.CharField(max_length=32)  # Key identifier
    is_encrypted = models.BooleanField(default=True)
    virus_scanned = models.BooleanField(default=False)
    security_score = models.PositiveIntegerField(default=0)  # 0-100
    
    # Storage information
    vault_path = models.CharField(max_length=500)  # Relative path in vault
    storage_backend = models.CharField(max_length=50, default='local_vault')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_from_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Access tracking
    last_accessed = models.DateTimeField(null=True, blank=True)
    access_count = models.PositiveIntegerField(default=0)
    
    # Status flags
    is_active = models.BooleanField(default=True)
    is_shared = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['file_id']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.user.email})"
    
    @property
    def display_name(self):
        """Generate user-friendly display name"""
        return f"{self.original_filename}"
    
    @property
    def size_display(self):
        """Human-readable file size"""
        size_bytes = self.file_size
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes // 1024} KB"
        else:
            return f"{size_bytes // (1024 * 1024)} MB"
    
    @property
    def full_vault_path(self):
        """Get full path to encrypted file"""
        from django.conf import settings
        return os.path.join(settings.MEDIA_ROOT, 'secure_medical_vault', self.secure_filename)
    
    def mark_accessed(self):
        """Track file access"""
        self.last_accessed = timezone.now()
        self.access_count += 1
        self.save(update_fields=['last_accessed', 'access_count'])
    
    def soft_delete(self):
        """Soft delete (mark as inactive)"""
        self.is_active = False
        self.save(update_fields=['is_active'])


class DocumentAccessLog(models.Model):
    """📊 Audit Trail for Document Access"""
    
    ACTION_CHOICES = [
        ('upload', 'File Upload'),
        ('view', 'File View'),
        ('download', 'File Download'),
        ('share', 'File Share'),
        ('delete', 'File Delete'),
        ('access_denied', 'Access Denied'),
    ]
    
    document = models.ForeignKey(SecureDocument, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # Request information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Additional context
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['document', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        user_info = self.user.email if self.user else 'Anonymous'
        return f"{self.action} - {self.document.original_filename} by {user_info}"


class DocumentShare(models.Model):
    """📤 Secure Document Sharing System"""
    
    SHARE_TYPE_CHOICES = [
        ('doctor', 'Doctor Access'),
        ('appointment', 'Appointment Specific'),
        ('temporary', 'Temporary Link'),
        ('emergency', 'Emergency Access'),
    ]
    
    document = models.ForeignKey(SecureDocument, on_delete=models.CASCADE, related_name='shares')
    shared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_documents')
    
    # Share configuration
    share_type = models.CharField(max_length=20, choices=SHARE_TYPE_CHOICES)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Access control
    allowed_email = models.EmailField(blank=True)  # Specific doctor email
    max_accesses = models.PositiveIntegerField(default=1)
    current_accesses = models.PositiveIntegerField(default=0)
    
    # Time limits
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_revoked = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['share_token']),
            models.Index(fields=['document', 'is_active']),
            models.Index(fields=['expires_at', 'is_active']),
        ]
    
    def __str__(self):
        return f"Share: {self.document.original_filename} -> {self.allowed_email}"
    
    @property
    def is_expired(self):
        """Check if share has expired"""
        return timezone.now() > self.expires_at
    
    @property
    def is_access_exhausted(self):
        """Check if access limit reached"""
        return self.current_accesses >= self.max_accesses
    
    @property
    def is_valid(self):
        """Check if share is still valid"""
        return (self.is_active and 
                not self.is_revoked and 
                not self.is_expired and 
                not self.is_access_exhausted)
    
    def use_access(self):
        """Record access use"""
        self.current_accesses += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['current_accesses', 'last_accessed'])
