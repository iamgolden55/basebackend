from django.db import models
from django.utils import timezone
from api.models.base import TimestampedModel
import uuid
import json
from cryptography.fernet import Fernet
from django.conf import settings
import base64


class Message(TimestampedModel):
    """
    WhatsApp-style message model with healthcare-grade encryption
    Supports text, files, voice messages, and medical context
    """
    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('file', 'File Attachment'),
        ('image', 'Image'),
        ('voice', 'Voice Message'),
        ('video', 'Video Message'),
        ('location', 'Location'),
        ('system', 'System Message'),
        ('emergency_alert', 'Emergency Alert'),
    ]
    
    MESSAGE_STATUS = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    PRIORITY_LEVELS = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    conversation = models.ForeignKey(
        'Conversation',
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    # Message content (encrypted)
    encrypted_content = models.TextField()  # AES-256 encrypted content
    content_hash = models.CharField(max_length=64)  # SHA-256 hash for integrity
    
    # Message metadata
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    status = models.CharField(max_length=20, choices=MESSAGE_STATUS, default='sent')
    priority_level = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='routine')
    
    # WhatsApp-style features
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_forwarded = models.BooleanField(default=False)
    
    # Healthcare-specific fields
    patient_context = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        related_name='related_messages',
        null=True,
        blank=True,
        help_text="Patient this message relates to"
    )
    appointment_context = models.ForeignKey(
        'Appointment',
        on_delete=models.SET_NULL,
        related_name='related_messages',
        null=True,
        blank=True
    )
    department_context = models.CharField(max_length=100, blank=True, null=True)
    
    # Delivery tracking
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Security and compliance
    is_encrypted = models.BooleanField(default=True)
    encryption_version = models.CharField(max_length=10, default='v1')
    requires_audit = models.BooleanField(default=True)
    
    # File-specific fields (for file/image/voice messages)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=100, blank=True, null=True)
    duration = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in seconds for voice/video")
    
    class Meta:
        db_table = 'messaging_message'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['status', 'priority_level']),
            models.Index(fields=['message_type', 'created_at']),
            models.Index(fields=['patient_context', 'appointment_context']),
            models.Index(fields=['is_deleted', 'created_at']),
        ]
    
    def __str__(self):
        if self.is_deleted:
            return f"[DELETED] Message from {self.sender.get_full_name()}"
        content_preview = self.get_content()[:50] if self.message_type == 'text' else f"[{self.get_message_type_display()}]"
        return f"{self.sender.get_full_name()}: {content_preview}"
    
    def save(self, *args, **kwargs):
        """Override save to ensure content is encrypted"""
        if hasattr(self, '_content_to_encrypt'):
            self.encrypted_content = self._encrypt_content(self._content_to_encrypt)
            self.content_hash = self._generate_content_hash(self._content_to_encrypt)
            delattr(self, '_content_to_encrypt')
        super().save(*args, **kwargs)
    
    def set_content(self, content):
        """Set message content (will be encrypted on save)"""
        self._content_to_encrypt = content
    
    def get_content(self):
        """Decrypt and return message content"""
        if not self.encrypted_content:
            return ""
        try:
            return self._decrypt_content(self.encrypted_content)
        except Exception as e:
            # Log the error for security monitoring
            import logging
            logger = logging.getLogger('messaging.security')
            logger.error(f"Failed to decrypt message {self.id}: {str(e)}")
            return "[DECRYPTION_ERROR]"
    
    def _get_encryption_key(self):
        """Get encryption key from settings"""
        # In production, this should come from a secure key management service
        key = getattr(settings, 'MESSAGE_ENCRYPTION_KEY', None)
        if not key:
            # Generate a key for development (DO NOT use in production)
            key = Fernet.generate_key()
        
        if isinstance(key, str):
            key = key.encode()
        
        return key
    
    def _encrypt_content(self, content):
        """Encrypt message content using AES-256"""
        if not content:
            return ""
        
        try:
            # Convert content to JSON string if it's not already a string
            if not isinstance(content, str):
                content = json.dumps(content)
            
            # Create Fernet cipher
            key = self._get_encryption_key()
            cipher = Fernet(key)
            
            # Encrypt content
            encrypted_bytes = cipher.encrypt(content.encode('utf-8'))
            
            # Return base64 encoded string for database storage
            return base64.b64encode(encrypted_bytes).decode('utf-8')
            
        except Exception as e:
            import logging
            logger = logging.getLogger('messaging.security')
            logger.error(f"Failed to encrypt message content: {str(e)}")
            raise
    
    def _decrypt_content(self, encrypted_content):
        """Decrypt message content"""
        if not encrypted_content:
            return ""
        
        try:
            # Create Fernet cipher
            key = self._get_encryption_key()
            cipher = Fernet(key)
            
            # Decode from base64 and decrypt
            encrypted_bytes = base64.b64decode(encrypted_content.encode('utf-8'))
            decrypted_bytes = cipher.decrypt(encrypted_bytes)
            
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            import logging
            logger = logging.getLogger('messaging.security')
            logger.error(f"Failed to decrypt message content: {str(e)}")
            raise
    
    def _generate_content_hash(self, content):
        """Generate SHA-256 hash of content for integrity verification"""
        import hashlib
        if not isinstance(content, str):
            content = json.dumps(content)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def verify_content_integrity(self):
        """Verify message content hasn't been tampered with"""
        try:
            current_content = self.get_content()
            current_hash = self._generate_content_hash(current_content)
            return current_hash == self.content_hash
        except Exception:
            return False
    
    def mark_as_delivered(self):
        """Mark message as delivered"""
        if self.status == 'sent':
            self.status = 'delivered'
            self.delivered_at = timezone.now()
            self.save(update_fields=['status', 'delivered_at'])
    
    def mark_as_read(self):
        """Mark message as read"""
        if self.status in ['sent', 'delivered']:
            self.status = 'read'
            self.read_at = timezone.now()
            if not self.delivered_at:
                self.delivered_at = timezone.now()
            self.save(update_fields=['status', 'read_at', 'delivered_at'])
    
    def soft_delete(self):
        """Soft delete message (WhatsApp-style delete for me)"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def edit_content(self, new_content):
        """Edit message content (WhatsApp-style edit)"""
        self.set_content(new_content)
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save()
    
    def get_medical_context(self):
        """Get medical context summary"""
        context = {}
        if self.patient_context:
            context['patient'] = {
                'id': self.patient_context.id,
                'name': self.patient_context.get_full_name(),
                'hpn': getattr(self.patient_context, 'hpn', None)
            }
        if self.appointment_context:
            context['appointment'] = {
                'id': self.appointment_context.id,
                'date': self.appointment_context.appointment_date,
                'doctor': self.appointment_context.doctor.name if self.appointment_context.doctor else None
            }
        if self.department_context:
            context['department'] = self.department_context
        return context
    
    @property
    def is_priority(self):
        """Check if message is high priority"""
        return self.priority_level in ['urgent', 'emergency']
    
    @property
    def age_in_hours(self):
        """Get message age in hours"""
        return (timezone.now() - self.created_at).total_seconds() / 3600
    
    def should_auto_delete(self):
        """Check if message should be auto-deleted based on retention policy"""
        if not self.conversation.auto_delete_enabled:
            return False
        
        retention_hours = self.conversation.retention_days * 24
        return self.age_in_hours > retention_hours