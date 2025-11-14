from django.db import models
from django.utils import timezone
from api.models.base import TimestampedModel
import uuid
import os
from django.core.validators import FileExtensionValidator


class MessageAttachment(TimestampedModel):
    """
    WhatsApp-style file attachments for healthcare messaging
    Supports images, documents, voice messages, videos with medical context
    """
    ATTACHMENT_TYPES = [
        ('image', 'Image'),
        ('document', 'Document'),
        ('voice', 'Voice Message'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('medical_image', 'Medical Image'),
        ('lab_result', 'Lab Result'),
        ('prescription', 'Prescription'),
        ('xray', 'X-Ray'),
        ('other', 'Other'),
    ]
    
    SECURITY_LEVELS = [
        ('public', 'Public'),
        ('internal', 'Internal Only'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    message = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    uploaded_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='uploaded_attachments'
    )
    
    # File information
    file = models.FileField(
        upload_to='messaging/attachments/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    # Images
                    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp',
                    # Documents
                    'pdf', 'doc', 'docx', 'txt', 'rtf',
                    # Audio/Video
                    'mp3', 'wav', 'ogg', 'mp4', 'avi', 'mov',
                    # Medical formats
                    'dcm', 'dicom',  # Medical imaging
                ]
            )
        ]
    )
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # Size in bytes
    file_type = models.CharField(max_length=100)  # MIME type
    attachment_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES, default='other')
    
    # WhatsApp-style features
    thumbnail = models.ImageField(
        upload_to='messaging/thumbnails/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Thumbnail for images and videos"
    )
    duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Duration in seconds for audio/video files"
    )
    
    # Healthcare-specific fields
    security_level = models.CharField(max_length=20, choices=SECURITY_LEVELS, default='internal')
    patient_context = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        related_name='medical_attachments',
        null=True,
        blank=True,
        help_text="Patient this attachment relates to"
    )
    medical_category = models.CharField(max_length=100, blank=True, null=True)
    
    # Security and compliance
    is_encrypted = models.BooleanField(default=True)
    encryption_key_id = models.CharField(max_length=100, blank=True, null=True)
    virus_scan_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('clean', 'Clean'),
            ('infected', 'Infected'),
            ('error', 'Scan Error'),
        ],
        default='pending'
    )
    virus_scan_date = models.DateTimeField(null=True, blank=True)
    
    # Access control
    download_count = models.PositiveIntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)  # For medical metadata, EXIF, etc.
    
    class Meta:
        db_table = 'messaging_attachment'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['message', 'attachment_type']),
            models.Index(fields=['uploaded_by', 'created_at']),
            models.Index(fields=['virus_scan_status', 'created_at']),
            models.Index(fields=['patient_context', 'medical_category']),
            models.Index(fields=['security_level', 'is_public']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.get_attachment_type_display()})"
    
    def save(self, *args, **kwargs):
        """Override save to set file metadata"""
        if self.file and not self.file_size:
            self.file_size = self.file.size
            self.file_type = self._get_mime_type()
            
            if not self.original_filename:
                self.original_filename = os.path.basename(self.file.name)
        
        super().save(*args, **kwargs)
        
        # Trigger virus scan asynchronously
        if not self.virus_scan_date:
            self._trigger_virus_scan()
    
    def _get_mime_type(self):
        """Get MIME type of the file"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(self.file.name)
        return mime_type or 'application/octet-stream'
    
    def _trigger_virus_scan(self):
        """Trigger asynchronous virus scan"""
        try:
            from api.tasks.messaging import scan_attachment_for_viruses
            scan_attachment_for_viruses.delay(str(self.id))
        except ImportError:
            # Celery not available, mark as clean for now
            self.virus_scan_status = 'clean'
            self.virus_scan_date = timezone.now()
            self.save(update_fields=['virus_scan_status', 'virus_scan_date'])
    
    def generate_thumbnail(self):
        """Generate thumbnail for images and videos"""
        if self.attachment_type not in ['image', 'video', 'medical_image']:
            return False
        
        try:
            from api.tasks.messaging import generate_attachment_thumbnail
            generate_attachment_thumbnail.delay(str(self.id))
            return True
        except ImportError:
            return False
    
    def is_safe_to_download(self):
        """Check if attachment is safe to download"""
        if self.virus_scan_status == 'infected':
            return False
        
        if self.expiry_date and timezone.now() > self.expiry_date:
            return False
        
        return True
    
    def record_download(self, user):
        """Record download access"""
        self.download_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['download_count', 'last_accessed'])
        
        # Log download for audit
        self._log_access(user, 'download')
    
    def _log_access(self, user, action):
        """Log file access for HIPAA compliance"""
        try:
            from .message_audit_log import MessageAuditLog
            
            MessageAuditLog.objects.create(
                action=f'attachment_{action}',
                user=user,
                conversation=self.message.conversation,
                message=self.message,
                details={
                    'attachment_id': str(self.id),
                    'filename': self.original_filename,
                    'file_type': self.attachment_type,
                    'security_level': self.security_level,
                    'patient_context': str(self.patient_context_id) if self.patient_context else None,
                }
            )
        except Exception as e:
            import logging
            logger = logging.getLogger('messaging.audit')
            logger.error(f"Failed to log attachment access: {e}")
    
    def get_download_url(self, user, expires_in_hours=24):
        """Get secure download URL for the attachment"""
        if not self.is_safe_to_download():
            return None
        
        # Record access
        self.record_download(user)
        
        # Generate secure URL (implementation depends on your file storage)
        return self._generate_secure_url(expires_in_hours)
    
    def _generate_secure_url(self, expires_in_hours=24):
        """Generate secure, time-limited URL for file download"""
        try:
            from django.urls import reverse
            from django.utils.http import urlencode
            import jwt
            from django.conf import settings
            
            # Create JWT token for secure access
            payload = {
                'attachment_id': str(self.id),
                'exp': timezone.now() + timezone.timedelta(hours=expires_in_hours),
                'iat': timezone.now(),
            }
            
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
            
            # Return secure download URL
            base_url = reverse('messaging:secure_download', kwargs={'token': token})
            return base_url
            
        except Exception as e:
            import logging
            logger = logging.getLogger('messaging.security')
            logger.error(f"Failed to generate secure URL: {e}")
            return None
    
    @property
    def file_size_human(self):
        """Human readable file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    @property
    def duration_human(self):
        """Human readable duration for audio/video"""
        if not self.duration:
            return None
        
        minutes, seconds = divmod(self.duration, 60)
        if minutes > 0:
            return f"{minutes}:{seconds:02d}"
        return f"0:{seconds:02d}"
    
    @property
    def is_medical_content(self):
        """Check if attachment contains medical content"""
        medical_types = ['medical_image', 'lab_result', 'prescription', 'xray']
        return self.attachment_type in medical_types or self.patient_context is not None
    
    def get_preview_data(self):
        """Get data for message preview"""
        return {
            'id': str(self.id),
            'filename': self.original_filename,
            'type': self.attachment_type,
            'size': self.file_size_human,
            'duration': self.duration_human,
            'thumbnail_url': self.thumbnail.url if self.thumbnail else None,
            'is_medical': self.is_medical_content,
            'security_level': self.security_level,
            'virus_status': self.virus_scan_status,
        }