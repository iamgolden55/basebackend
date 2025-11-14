from django.db import models
from django.utils import timezone
from api.models.base import TimestampedModel
import uuid


class Conversation(TimestampedModel):
    """
    WhatsApp-style conversation model for healthcare messaging
    Supports both direct messages and group chats
    """
    CONVERSATION_TYPES = [
        ('direct', 'Direct Message'),
        ('group', 'Group Chat'),
        ('department', 'Department Channel'),
        ('emergency', 'Emergency Channel'),
        ('broadcast', 'Broadcast Channel'),
    ]
    
    PRIORITY_LEVELS = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation_type = models.CharField(max_length=20, choices=CONVERSATION_TYPES, default='direct')
    
    # Conversation metadata
    title = models.CharField(max_length=200, blank=True, null=True)  # For group chats
    description = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='messaging/avatars/', blank=True, null=True)
    
    # Healthcare-specific fields
    priority_level = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='routine')
    department = models.CharField(max_length=100, blank=True, null=True)  # ICU, Emergency, etc.
    hospital_context = models.ForeignKey(
        'Hospital', 
        on_delete=models.CASCADE, 
        related_name='conversations',
        blank=True, 
        null=True
    )
    
    # WhatsApp-style features
    is_muted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    
    # Security and compliance
    is_encrypted = models.BooleanField(default=True)
    retention_days = models.PositiveIntegerField(default=2555)  # 7 years for medical records
    auto_delete_enabled = models.BooleanField(default=False)
    
    # Activity tracking
    last_message_at = models.DateTimeField(default=timezone.now)
    last_activity_at = models.DateTimeField(auto_now=True)
    
    # Admin features
    created_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        related_name='created_conversations',
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'messaging_conversation'
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['conversation_type', 'hospital_context']),
            models.Index(fields=['priority_level', 'department']),
            models.Index(fields=['last_message_at']),
            models.Index(fields=['is_archived', 'is_muted']),
        ]
    
    def __str__(self):
        if self.title:
            return f"{self.get_conversation_type_display()}: {self.title}"
        elif self.conversation_type == 'direct':
            participants = self.participants.all()[:2]
            if len(participants) >= 2:
                return f"Direct: {participants[0].user.get_full_name()} & {participants[1].user.get_full_name()}"
            elif len(participants) == 1:
                return f"Direct: {participants[0].user.get_full_name()}"
        return f"{self.get_conversation_type_display()} - {self.id}"
    
    @property
    def participant_count(self):
        """Get number of active participants"""
        return self.participants.filter(is_active=True).count()
    
    @property
    def unread_count(self):
        """Get total unread messages across all participants"""
        return sum(p.unread_count for p in self.participants.all())
    
    @property
    def last_message(self):
        """Get the latest message in this conversation"""
        return self.messages.order_by('-created_at').first()
    
    def get_participants_for_user(self, user):
        """Get other participants in conversation (excluding the user)"""
        return self.participants.filter(is_active=True).exclude(user=user)
    
    def mark_as_read_for_user(self, user):
        """Mark all messages as read for a specific user"""
        participant = self.participants.filter(user=user).first()
        if participant:
            participant.last_read_at = timezone.now()
            participant.unread_count = 0
            participant.save(update_fields=['last_read_at', 'unread_count'])
    
    def add_participant(self, user, role='member'):
        """Add a new participant to the conversation"""
        from .message_participant import MessageParticipant
        participant, created = MessageParticipant.objects.get_or_create(
            conversation=self,
            user=user,
            defaults={'role': role, 'is_active': True}
        )
        if not created and not participant.is_active:
            participant.is_active = True
            participant.save(update_fields=['is_active'])
        return participant
    
    def remove_participant(self, user):
        """Remove a participant from the conversation"""
        participant = self.participants.filter(user=user).first()
        if participant:
            participant.is_active = False
            participant.save(update_fields=['is_active'])
    
    def update_last_message_time(self):
        """Update the last message timestamp"""
        self.last_message_at = timezone.now()
        self.save(update_fields=['last_message_at'])
    
    def is_participant(self, user):
        """Check if user is an active participant"""
        return self.participants.filter(user=user, is_active=True).exists()
    
    def get_conversation_name_for_user(self, user):
        """Get display name for conversation from user's perspective"""
        if self.title:
            return self.title
        elif self.conversation_type == 'direct':
            other_participants = self.get_participants_for_user(user)
            if other_participants.exists():
                return other_participants.first().user.get_full_name()
            return "Direct Message"
        elif self.conversation_type == 'department':
            return f"{self.department} Department"
        return self.get_conversation_type_display()