from django.db import models
from django.utils import timezone
from api.models.base import TimestampedModel
import uuid


class MessageParticipant(TimestampedModel):
    """
    WhatsApp-style participant model for conversation management
    Tracks user participation, read receipts, and notification preferences
    """
    PARTICIPANT_ROLES = [
        ('member', 'Member'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('owner', 'Owner'),
        ('observer', 'Observer'),  # Can read but not send
    ]
    
    NOTIFICATION_SETTINGS = [
        ('all', 'All Messages'),
        ('mentions', 'Mentions Only'),
        ('none', 'No Notifications'),
        ('emergency_only', 'Emergency Only'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    conversation = models.ForeignKey(
        'Conversation',
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='message_participations'
    )
    
    # Participant status
    role = models.CharField(max_length=20, choices=PARTICIPANT_ROLES, default='member')
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(default=timezone.now)
    left_at = models.DateTimeField(null=True, blank=True)
    
    # WhatsApp-style read tracking
    last_read_at = models.DateTimeField(default=timezone.now)
    last_message_read_id = models.UUIDField(null=True, blank=True)  # Last message read
    unread_count = models.PositiveIntegerField(default=0)
    
    # WhatsApp-style activity tracking
    last_seen_at = models.DateTimeField(default=timezone.now)
    is_typing = models.BooleanField(default=False)
    typing_started_at = models.DateTimeField(null=True, blank=True)
    
    # Notification preferences
    notifications = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_SETTINGS, 
        default='all'
    )
    is_muted = models.BooleanField(default=False)
    muted_until = models.DateTimeField(null=True, blank=True)
    
    # Healthcare-specific settings
    emergency_notifications = models.BooleanField(default=True)
    department_notifications = models.BooleanField(default=True)
    
    # Privacy and security
    can_add_participants = models.BooleanField(default=True)
    can_edit_conversation = models.BooleanField(default=False)
    can_delete_messages = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'messaging_participant'
        unique_together = ['conversation', 'user']
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['conversation', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['last_read_at', 'unread_count']),
            models.Index(fields=['is_typing', 'typing_started_at']),
            models.Index(fields=['role', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} in {self.conversation}"
    
    def mark_message_as_read(self, message):
        """Mark a specific message as read and update counters"""
        if message.conversation_id != self.conversation_id:
            return False
        
        # Update read tracking
        self.last_read_at = timezone.now()
        self.last_message_read_id = message.id
        
        # Update unread count (count messages after this one)
        from .message import Message
        self.unread_count = Message.objects.filter(
            conversation=self.conversation,
            created_at__gt=message.created_at,
            is_deleted=False
        ).exclude(sender=self.user).count()
        
        self.save(update_fields=['last_read_at', 'last_message_read_id', 'unread_count'])
        return True
    
    def increment_unread_count(self):
        """Increment unread count when new message arrives"""
        self.unread_count = models.F('unread_count') + 1
        self.save(update_fields=['unread_count'])
    
    def reset_unread_count(self):
        """Reset unread count to zero"""
        self.unread_count = 0
        self.save(update_fields=['unread_count'])
    
    def start_typing(self):
        """Mark user as typing in this conversation"""
        self.is_typing = True
        self.typing_started_at = timezone.now()
        self.save(update_fields=['is_typing', 'typing_started_at'])
    
    def stop_typing(self):
        """Mark user as stopped typing"""
        self.is_typing = False
        self.typing_started_at = None
        self.save(update_fields=['is_typing', 'typing_started_at'])
    
    def update_last_seen(self):
        """Update last seen timestamp"""
        self.last_seen_at = timezone.now()
        self.save(update_fields=['last_seen_at'])
    
    def leave_conversation(self):
        """Leave the conversation (soft delete)"""
        self.is_active = False
        self.left_at = timezone.now()
        self.save(update_fields=['is_active', 'left_at'])
    
    def rejoin_conversation(self):
        """Rejoin the conversation"""
        self.is_active = True
        self.left_at = None
        self.joined_at = timezone.now()
        self.save(update_fields=['is_active', 'left_at', 'joined_at'])
    
    def mute_temporarily(self, hours=8):
        """Mute notifications for specified hours"""
        self.is_muted = True
        self.muted_until = timezone.now() + timezone.timedelta(hours=hours)
        self.save(update_fields=['is_muted', 'muted_until'])
    
    def unmute(self):
        """Unmute notifications"""
        self.is_muted = False
        self.muted_until = None
        self.save(update_fields=['is_muted', 'muted_until'])
    
    @property
    def is_muted_now(self):
        """Check if currently muted (considering temporary muting)"""
        if not self.is_muted:
            return False
        
        if self.muted_until and timezone.now() > self.muted_until:
            # Temporary mute expired, auto-unmute
            self.unmute()
            return False
        
        return True
    
    @property
    def should_receive_notifications(self):
        """Check if participant should receive notifications"""
        if self.is_muted_now:
            return False
        
        if self.notifications == 'none':
            return False
        
        return True
    
    @property
    def should_receive_emergency_notifications(self):
        """Check if should receive emergency notifications (bypasses muting)"""
        return self.emergency_notifications
    
    def has_permission(self, action):
        """Check if participant has permission for specific action"""
        permissions = {
            'send_message': self.is_active,
            'add_participants': self.can_add_participants and self.role in ['admin', 'owner', 'moderator'],
            'edit_conversation': self.can_edit_conversation and self.role in ['admin', 'owner'],
            'delete_messages': self.can_delete_messages and self.role in ['admin', 'owner'],
            'manage_participants': self.role in ['owner', 'admin'],
            'delete_conversation': self.role == 'owner',
        }
        return permissions.get(action, False)
    
    def get_unread_messages(self):
        """Get unread messages for this participant"""
        from .message import Message
        
        last_read_time = self.last_read_at
        if self.last_message_read_id:
            try:
                last_read_message = Message.objects.get(id=self.last_message_read_id)
                last_read_time = last_read_message.created_at
            except Message.DoesNotExist:
                pass
        
        return Message.objects.filter(
            conversation=self.conversation,
            created_at__gt=last_read_time,
            is_deleted=False
        ).exclude(sender=self.user).order_by('created_at')
    
    def get_read_status_for_message(self, message):
        """Get read status for a specific message"""
        if message.sender_id == self.user_id:
            return 'sent'  # Own message
        
        if self.last_message_read_id == message.id:
            return 'read'
        
        if self.last_read_at >= message.created_at:
            return 'read'
        
        return 'unread'