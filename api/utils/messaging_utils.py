"""
Utility functions for healthcare messaging system

This module provides helper functions for sending real-time notifications,
managing presence, and handling WhatsApp-style messaging features.
"""

import json
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from typing import List, Dict, Optional

logger = logging.getLogger('messaging.utils')
channel_layer = get_channel_layer()


class MessagingNotifier:
    """
    Utility class for sending real-time notifications through WebSocket
    """
    
    @staticmethod
    def send_emergency_alert(user_ids: List[str], title: str, message: str, 
                           conversation_id: Optional[str] = None, actions: List[Dict] = None):
        """
        Send emergency alert to specific users
        
        Args:
            user_ids: List of user IDs to notify
            title: Alert title
            message: Alert message
            conversation_id: Optional conversation ID
            actions: Optional list of action buttons
        """
        try:
            for user_id in user_ids:
                async_to_sync(channel_layer.group_send)(
                    f'notifications_{user_id}',
                    {
                        'type': 'emergency_notification',
                        'title': title,
                        'message': message,
                        'timestamp': timezone.now().isoformat(),
                        'conversation_id': conversation_id,
                        'actions': actions or []
                    }
                )
            
            logger.info(f"Emergency alert sent to {len(user_ids)} users: {title}")
            
        except Exception as e:
            logger.error(f"Failed to send emergency alert: {e}")
    
    @staticmethod
    def send_mention_notification(user_id: str, conversation_id: str, 
                                sender_name: str, message_preview: str):
        """
        Send mention notification to a user
        
        Args:
            user_id: User ID to notify
            conversation_id: Conversation where mention occurred
            sender_name: Name of user who mentioned
            message_preview: Preview of the message
        """
        try:
            async_to_sync(channel_layer.group_send)(
                f'notifications_{user_id}',
                {
                    'type': 'mention_notification',
                    'message': f"{sender_name} mentioned you: {message_preview}",
                    'conversation_id': conversation_id,
                    'sender_name': sender_name,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            logger.info(f"Mention notification sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send mention notification: {e}")
    
    @staticmethod
    def send_system_notification(user_ids: List[str], title: str, message: str, 
                               category: str = 'info'):
        """
        Send system notification to users
        
        Args:
            user_ids: List of user IDs to notify
            title: Notification title
            message: Notification message
            category: Notification category (info, warning, success, error)
        """
        try:
            for user_id in user_ids:
                async_to_sync(channel_layer.group_send)(
                    f'notifications_{user_id}',
                    {
                        'type': 'system_notification',
                        'title': title,
                        'message': message,
                        'category': category,
                        'timestamp': timezone.now().isoformat()
                    }
                )
            
            logger.info(f"System notification sent to {len(user_ids)} users: {title}")
            
        except Exception as e:
            logger.error(f"Failed to send system notification: {e}")
    
    @staticmethod
    def broadcast_to_conversation(conversation_id: str, message_data: Dict):
        """
        Broadcast message to all participants in a conversation
        
        Args:
            conversation_id: Conversation ID
            message_data: Message data to broadcast
        """
        try:
            async_to_sync(channel_layer.group_send)(
                f'chat_{conversation_id}',
                {
                    'type': 'chat_message',
                    'message': message_data,
                    'sender_id': message_data.get('sender', {}).get('id')
                }
            )
            
            logger.info(f"Message broadcasted to conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
    
    @staticmethod
    def update_typing_status(conversation_id: str, user_id: str, user_name: str, is_typing: bool):
        """
        Update typing status for a conversation
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            user_name: User's display name
            is_typing: Whether user is typing
        """
        try:
            async_to_sync(channel_layer.group_send)(
                f'typing_{conversation_id}',
                {
                    'type': 'typing_status',
                    'user_id': user_id,
                    'user_name': user_name,
                    'is_typing': is_typing,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to update typing status: {e}")
    
    @staticmethod
    def update_presence(user_id: str, status: str, last_seen: str = None):
        """
        Update user presence status
        
        Args:
            user_id: User ID
            status: Presence status (online, offline, away)
            last_seen: Last seen timestamp
        """
        try:
            async_to_sync(channel_layer.group_send)(
                f'presence_{user_id}',
                {
                    'type': 'presence_update',
                    'user_id': user_id,
                    'status': status,
                    'last_seen': last_seen or timezone.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to update presence: {e}")


class MessageProcessor:
    """
    Utility class for processing messages and extracting features
    """
    
    @staticmethod
    def extract_mentions(content: str) -> List[str]:
        """
        Extract @mentions from message content
        
        Args:
            content: Message content
            
        Returns:
            List of mentioned usernames/IDs
        """
        import re
        
        # Extract @username patterns
        mentions = re.findall(r'@(\w+)', content)
        return mentions
    
    @staticmethod
    def detect_emergency_keywords(content: str) -> bool:
        """
        Detect emergency keywords in message content
        
        Args:
            content: Message content
            
        Returns:
            True if emergency keywords detected
        """
        emergency_keywords = [
            'emergency', 'urgent', 'critical', 'code red', 'help',
            'cardiac arrest', 'stroke', 'trauma', 'respiratory distress',
            'severe bleeding', 'unconscious', 'overdose', 'allergic reaction'
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in emergency_keywords)
    
    @staticmethod
    def extract_patient_references(content: str) -> List[str]:
        """
        Extract patient HPN references from message content
        
        Args:
            content: Message content
            
        Returns:
            List of HPN references found
        """
        import re
        
        # Extract HPN patterns (e.g., HPN123456, HPN 123 456)
        hpn_patterns = re.findall(r'HPN\s*(\d{3}\s*\d{3}\s*\d{4})', content, re.IGNORECASE)
        return hpn_patterns
    
    @staticmethod
    def format_message_preview(content: str, max_length: int = 100) -> str:
        """
        Format message content for preview/notification
        
        Args:
            content: Full message content
            max_length: Maximum preview length
            
        Returns:
            Formatted preview
        """
        if len(content) <= max_length:
            return content
        
        return content[:max_length - 3] + '...'
    
    @staticmethod
    def sanitize_message_content(content: str) -> str:
        """
        Sanitize message content for security
        
        Args:
            content: Raw message content
            
        Returns:
            Sanitized content
        """
        import html
        
        # HTML escape to prevent XSS
        sanitized = html.escape(content)
        
        # Remove potential script tags
        import re
        sanitized = re.sub(r'<script.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        return sanitized.strip()


class ConversationUtils:
    """
    Utility functions for conversation management
    """
    
    @staticmethod
    def create_emergency_conversation(creator_user, hospital, emergency_type: str, 
                                    initial_message: str) -> Optional[str]:
        """
        Create an emergency conversation with appropriate participants
        
        Args:
            creator_user: User creating the emergency conversation
            hospital: Hospital context
            emergency_type: Type of emergency (cardiac, trauma, etc.)
            initial_message: Initial emergency message
            
        Returns:
            Conversation ID if created successfully
        """
        try:
            from api.models.messaging import Conversation, MessageParticipant
            from api.models import CustomUser
            
            # Create emergency conversation
            conversation = Conversation.objects.create(
                title=f"Emergency: {emergency_type}",
                conversation_type='emergency',
                priority_level='emergency',
                hospital_context=hospital,
                created_by=creator_user,
                department=emergency_type
            )
            
            # Add creator as admin
            conversation.add_participant(creator_user, role='admin')
            
            # Add emergency response team (hospital admins, emergency department)
            emergency_users = CustomUser.objects.filter(
                role__in=['hospital_admin', 'doctor'],
                # Add additional filters for emergency team
            )
            
            for user in emergency_users:
                conversation.add_participant(user, role='member')
            
            # Send initial emergency message
            storage = get_auto_scaling_storage()
            message_data = {
                'conversation_id': str(conversation.id),
                'sender_id': str(creator_user.id),
                'content': initial_message,
                'message_type': 'emergency_alert',
                'priority_level': 'emergency',
                'created_at': timezone.now(),
            }
            
            message_id = storage.store_message(message_data)
            
            # Broadcast emergency alert
            MessagingNotifier.send_emergency_alert(
                user_ids=[str(user.id) for user in emergency_users],
                title=f"Emergency: {emergency_type}",
                message=initial_message,
                conversation_id=str(conversation.id),
                actions=[
                    {'label': 'Join Emergency Response', 'action': 'join_conversation'},
                    {'label': 'View Patient', 'action': 'view_patient'}
                ]
            )
            
            logger.info(f"Emergency conversation {conversation.id} created for {emergency_type}")
            return str(conversation.id)
            
        except Exception as e:
            logger.error(f"Failed to create emergency conversation: {e}")
            return None
    
    @staticmethod
    def get_conversation_participants_summary(conversation_id: str) -> Dict:
        """
        Get summary of conversation participants
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dictionary with participant summary
        """
        try:
            from api.models.messaging import MessageParticipant
            
            participants = MessageParticipant.objects.filter(
                conversation_id=conversation_id,
                is_active=True
            ).select_related('user')
            
            online_count = 0
            total_count = participants.count()
            
            for participant in participants:
                # Consider online if last seen within 5 minutes
                if participant.last_seen_at:
                    time_diff = timezone.now() - participant.last_seen_at
                    if time_diff.total_seconds() < 300:  # 5 minutes
                        online_count += 1
            
            return {
                'total_participants': total_count,
                'online_participants': online_count,
                'offline_participants': total_count - online_count,
                'participants': [
                    {
                        'user_id': str(p.user.id),
                        'name': p.user.get_full_name(),
                        'role': p.role,
                        'last_seen': p.last_seen_at.isoformat() if p.last_seen_at else None,
                        'unread_count': p.unread_count
                    } for p in participants
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get participants summary: {e}")
            return {}


# Helper functions for easy access
def send_emergency_alert(user_ids: List[str], title: str, message: str, **kwargs):
    """Shortcut for sending emergency alerts"""
    return MessagingNotifier.send_emergency_alert(user_ids, title, message, **kwargs)

def send_mention_notification(user_id: str, conversation_id: str, sender_name: str, message_preview: str):
    """Shortcut for sending mention notifications"""
    return MessagingNotifier.send_mention_notification(user_id, conversation_id, sender_name, message_preview)

def broadcast_message(conversation_id: str, message_data: Dict):
    """Shortcut for broadcasting messages"""
    return MessagingNotifier.broadcast_to_conversation(conversation_id, message_data)

def update_typing(conversation_id: str, user_id: str, user_name: str, is_typing: bool):
    """Shortcut for updating typing status"""
    return MessagingNotifier.update_typing_status(conversation_id, user_id, user_name, is_typing)