from django.db import models
from django.utils import timezone
from api.models.base import TimestampedModel
import uuid


class MessageMetadata(TimestampedModel):
    """
    Lightweight metadata model for hybrid storage strategy
    Stores minimal message info in local DB for fast queries
    while full message content is stored in cloud storage
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Reference to cloud storage
    firebase_id = models.CharField(max_length=100, unique=True, db_index=True)
    cloud_storage_provider = models.CharField(max_length=50, default='firebase')
    
    # Essential metadata for fast queries
    conversation_id = models.UUIDField(db_index=True)
    sender_id = models.UUIDField(db_index=True)
    message_type = models.CharField(max_length=20, default='text')
    priority_level = models.CharField(max_length=20, default='routine')
    
    # Timestamps
    message_created_at = models.DateTimeField(db_index=True)
    archived_at = models.DateTimeField(default=timezone.now)
    
    # Status tracking
    is_deleted = models.BooleanField(default=False)
    is_encrypted = models.BooleanField(default=True)
    
    # Search optimization
    content_preview = models.CharField(max_length=200, blank=True, null=True)
    has_attachments = models.BooleanField(default=False)
    attachment_count = models.PositiveIntegerField(default=0)
    
    # Medical context (for fast filtering)
    has_patient_context = models.BooleanField(default=False)
    patient_id = models.UUIDField(null=True, blank=True, db_index=True)
    department_context = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'messaging_metadata'
        ordering = ['-message_created_at']
        indexes = [
            models.Index(fields=['conversation_id', 'message_created_at']),
            models.Index(fields=['sender_id', 'message_created_at']),
            models.Index(fields=['firebase_id']),
            models.Index(fields=['message_type', 'priority_level']),
            models.Index(fields=['patient_id', 'has_patient_context']),
            models.Index(fields=['is_deleted', 'message_created_at']),
        ]
    
    def __str__(self):
        return f"Metadata for {self.firebase_id} ({self.message_type})"