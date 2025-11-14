"""
WebSocket consumers for real-time healthcare messaging

This module implements WhatsApp-style real-time messaging features:
- Instant message delivery
- Read receipts
- Typing indicators  
- Online presence
- Emergency notifications
"""

import json
import logging
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.conf import settings
from api.models.messaging import (
    Conversation, Message, MessageParticipant, MessageAuditLog,
    get_auto_scaling_storage
)
from api.models import CustomUser

logger = logging.getLogger('messaging.websocket')


class BaseMessagingConsumer(AsyncWebsocketConsumer):
    """
    Base consumer with common authentication and utility methods
    """
    
    def get_user_id(self):
        """Get user ID from user object (handles both id and hpn fields)"""
        if hasattr(self.user, 'id') and self.user.id:
            return str(self.user.id)
        elif hasattr(self.user, 'hpn') and self.user.hpn:
            return str(self.user.hpn)
        else:
            return str(self.user)
    
    async def connect(self):
        """Handle WebSocket connection with authentication"""
        self.user = self.scope.get('user')
        
        # Reject anonymous users
        if isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            logger.warning(f"Unauthenticated WebSocket connection attempt from {self.scope.get('client')}")
            await self.close(code=4001)  # Unauthorized
            return
        
        # Call subclass-specific connection logic
        await self.handle_connect()
    
    async def handle_connect(self):
        """Override in subclasses for specific connection logic"""
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        logger.info(f"User {self.get_user_id()} disconnected from {self.__class__.__name__} (code: {close_code})")
        await self.handle_disconnect(close_code)
    
    async def handle_disconnect(self, close_code):
        """Override in subclasses for specific disconnection logic"""
        pass
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Route to appropriate handler
            handler_name = f'handle_{message_type}'
            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                await handler(data)
            else:
                await self.send_error(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send_error("Internal server error")
    
    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def send_success(self, data=None):
        """Send success message to client"""
        response = {
            'type': 'success',
            'timestamp': timezone.now().isoformat()
        }
        if data:
            response.update(data)
        
        await self.send(text_data=json.dumps(response))


class ChatConsumer(BaseMessagingConsumer):
    """
    WebSocket consumer for real-time chat messaging
    Handles message sending, delivery receipts, and read receipts
    """
    
    async def handle_connect(self):
        """Connect to a specific conversation room"""
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        
        # Verify user has access to this conversation
        has_access = await self.verify_conversation_access()
        if not has_access:
            await self.close(code=4003)  # Forbidden
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Update user's last seen in this conversation
        await self.update_participant_presence()
        
        # Notify room that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_presence',
                'user_id': self.get_user_id(),
                'status': 'online',
                'timestamp': timezone.now().isoformat()
            }
        )
        
        logger.info(f"User {self.get_user_id()} connected to conversation {self.conversation_id}")
    
    async def handle_disconnect(self, close_code):
        """Leave conversation room"""
        # Only proceed if room_group_name was set (i.e., connection was successful)
        if hasattr(self, 'room_group_name') and hasattr(self, 'user') and self.user:
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            # Update last seen timestamp
            await self.update_participant_presence()
            
            # Notify room that user left
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_presence',
                    'user_id': self.get_user_id(),
                    'status': 'offline',
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    @database_sync_to_async
    def verify_conversation_access(self):
        """Verify user has access to the conversation"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.is_participant(self.user)
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def update_participant_presence(self):
        """Update participant's last seen timestamp"""
        try:
            participant = MessageParticipant.objects.get(
                conversation_id=self.conversation_id,
                user=self.user
            )
            participant.update_last_seen()
            return True
        except MessageParticipant.DoesNotExist:
            return False
    
    async def handle_send_message(self, data):
        """Handle sending a new message"""
        try:
            content = data.get('content', '').strip()
            message_type = data.get('message_type', 'text')
            priority_level = data.get('priority', 'routine')
            reply_to_id = data.get('reply_to')
            patient_context_id = data.get('patient_context')
            
            if not content and message_type == 'text':
                await self.send_error("Message content cannot be empty")
                return
            
            # Create message in database
            message_data = await self.create_message(
                content=content,
                message_type=message_type,
                priority_level=priority_level,
                reply_to_id=reply_to_id,
                patient_context_id=patient_context_id
            )
            
            if not message_data:
                await self.send_error("Failed to create message")
                return
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_data,
                    'sender_id': self.get_user_id()
                }
            )
            
            # Log message for audit
            await self.log_message_action('message_sent', message_data['id'])
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await self.send_error("Failed to send message")
    
    @database_sync_to_async
    def create_message(self, content, message_type='text', priority_level='routine', 
                      reply_to_id=None, patient_context_id=None):
        """Create message in database using auto-scaling storage"""
        try:
            # Get storage instance
            storage = get_auto_scaling_storage()
            
            # Prepare message data
            message_data = {
                'conversation_id': self.conversation_id,
                'sender_id': self.get_user_id(),
                'content': content,
                'message_type': message_type,
                'priority_level': priority_level,
                'created_at': timezone.now(),
            }
            
            # Add optional fields
            if reply_to_id:
                message_data['reply_to_id'] = reply_to_id
            
            if patient_context_id:
                try:
                    patient = CustomUser.objects.get(id=patient_context_id)
                    message_data['patient_context_id'] = patient_context_id
                except CustomUser.DoesNotExist:
                    pass
            
            # Store message using auto-scaling storage
            message_id = storage.store_message(message_data)
            
            # Update conversation last message time
            conversation = Conversation.objects.get(id=self.conversation_id)
            conversation.update_last_message_time()
            
            # Update unread counts for other participants
            participants = MessageParticipant.objects.filter(
                conversation_id=self.conversation_id,
                is_active=True
            ).exclude(user=self.user)
            
            for participant in participants:
                participant.increment_unread_count()
            
            # Return message data for broadcasting
            return {
                'id': message_id,
                'content': content,
                'message_type': message_type,
                'priority_level': priority_level,
                'sender': {
                    'id': self.get_user_id(),
                    'name': self.user.get_full_name(),
                    'role': getattr(self.user, 'role', 'user')
                },
                'timestamp': timezone.now().isoformat(),
                'reply_to_id': reply_to_id,
                'patient_context_id': patient_context_id,
                'status': 'sent'
            }
            
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None
    
    async def handle_mark_read(self, data):
        """Handle marking messages as read"""
        try:
            message_id = data.get('message_id')
            if not message_id:
                await self.send_error("Message ID required")
                return
            
            # Mark message as read
            success = await self.mark_message_read(message_id)
            
            if success:
                # Broadcast read receipt to other participants
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_read',
                        'message_id': message_id,
                        'reader_id': self.get_user_id(),
                        'timestamp': timezone.now().isoformat()
                    }
                )
                
                await self.send_success({'message_id': message_id, 'status': 'read'})
            else:
                await self.send_error("Failed to mark message as read")
                
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            await self.send_error("Failed to mark message as read")
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark a specific message as read by the current user"""
        try:
            # Get the participant
            participant = MessageParticipant.objects.get(
                conversation_id=self.conversation_id,
                user=self.user
            )
            
            # Get the message (simplified - in production you'd retrieve from storage)
            # For now, we'll just update the participant's read status
            participant.last_read_at = timezone.now()
            participant.last_message_read_id = message_id
            participant.save(update_fields=['last_read_at', 'last_message_read_id'])
            
            return True
            
        except MessageParticipant.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False
    
    @database_sync_to_async
    def log_message_action(self, action, message_id=None):
        """Log message action for audit purposes"""
        try:
            # Get conversation object for audit logging
            conversation = None
            try:
                conversation = Conversation.objects.get(id=self.conversation_id)
            except Conversation.DoesNotExist:
                pass
            
            MessageAuditLog.log_action(
                action=action,
                user=self.user,
                conversation=conversation,
                details={
                    'message_id': message_id,
                    'websocket_connection': True,
                    'user_agent': 'WebSocket',
                    'conversation_id': self.conversation_id  # Keep as backup in details
                }
            )
        except Exception as e:
            logger.error(f"Error logging message action: {e}")
    
    # WebSocket message handlers (called by channel layer)
    
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        message = event['message']
        sender_id = event['sender_id']
        
        # Don't send the message back to the sender
        if sender_id != self.get_user_id():
            await self.send(text_data=json.dumps({
                'type': 'new_message',
                'message': message
            }))
    
    async def message_read(self, event):
        """Send read receipt to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'message_id': event['message_id'],
            'reader_id': event['reader_id'],
            'timestamp': event['timestamp']
        }))
    
    async def user_presence(self, event):
        """Send user presence update to WebSocket"""
        # Don't send presence updates about yourself
        if event['user_id'] != self.get_user_id():
            await self.send(text_data=json.dumps({
                'type': 'user_presence',
                'user_id': event['user_id'],
                'status': event['status'],
                'timestamp': event['timestamp']
            }))


class TypingIndicatorConsumer(BaseMessagingConsumer):
    """
    WebSocket consumer for typing indicators
    Handles "user is typing..." functionality
    """
    
    async def handle_connect(self):
        """Connect to typing indicator room"""
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'typing_{self.conversation_id}'
        
        # Verify access
        has_access = await self.verify_conversation_access()
        if not has_access:
            await self.close(code=4003)
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def handle_disconnect(self, close_code):
        """Leave typing indicator room"""
        # Only proceed if room_group_name was set (i.e., connection was successful)
        if hasattr(self, 'room_group_name') and hasattr(self, 'user') and self.user:
            # Stop typing when disconnecting
            await self.set_typing_status(False)
            
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    @database_sync_to_async
    def verify_conversation_access(self):
        """Verify user has access to the conversation"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.is_participant(self.user)
        except Conversation.DoesNotExist:
            return False
    
    async def handle_start_typing(self, data):
        """Handle start typing indicator"""
        await self.set_typing_status(True)
    
    async def handle_stop_typing(self, data):
        """Handle stop typing indicator"""
        await self.set_typing_status(False)
    
    async def set_typing_status(self, is_typing):
        """Update typing status and broadcast to room"""
        try:
            # Update database
            await self.update_typing_status(is_typing)
            
            # Broadcast to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'user_id': self.get_user_id(),
                    'user_name': self.user.get_full_name(),
                    'is_typing': is_typing,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error setting typing status: {e}")
    
    @database_sync_to_async
    def update_typing_status(self, is_typing):
        """Update typing status in database"""
        try:
            participant = MessageParticipant.objects.get(
                conversation_id=self.conversation_id,
                user=self.user
            )
            
            if is_typing:
                participant.start_typing()
            else:
                participant.stop_typing()
                
            return True
            
        except MessageParticipant.DoesNotExist:
            return False
    
    async def typing_status(self, event):
        """Send typing status to WebSocket"""
        # Don't send typing updates about yourself
        if event['user_id'] != self.get_user_id():
            await self.send(text_data=json.dumps({
                'type': 'typing_status',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
                'timestamp': event['timestamp']
            }))


class PresenceConsumer(BaseMessagingConsumer):
    """
    WebSocket consumer for user presence (online/offline status)
    """
    
    async def handle_connect(self):
        """Connect to global presence updates"""
        user_id = self.get_user_id()
        self.room_group_name = f'presence_{user_id}'
        
        # Join user's personal presence group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Mark user as online
        await self.update_user_presence('online')
    
    async def handle_disconnect(self, close_code):
        """Handle presence disconnection"""
        # Only proceed if room_group_name was set (i.e., connection was successful)
        if hasattr(self, 'room_group_name') and hasattr(self, 'user') and self.user:
            # Mark user as offline
            await self.update_user_presence('offline')
            
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    @database_sync_to_async
    def update_user_presence(self, status):
        """Update user's online presence status"""
        try:
            # Update all user's conversation participations
            participants = MessageParticipant.objects.filter(
                user=self.user,
                is_active=True
            )
            
            for participant in participants:
                participant.update_last_seen()
            
            logger.info(f"User {self.get_user_id()} status updated to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user presence: {e}")
            return False
    
    async def presence_update(self, event):
        """Send presence update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'presence_update',
            'user_id': event['user_id'],
            'status': event['status'],
            'last_seen': event['last_seen']
        }))


class NotificationConsumer(BaseMessagingConsumer):
    """
    WebSocket consumer for real-time notifications
    Handles emergency alerts, mentions, and system notifications
    """
    
    async def handle_connect(self):
        """Connect to user's notification channel"""
        user_id = self.get_user_id()
        self.room_group_name = f'notifications_{user_id}'
        
        # Join user's notification group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.get_user_id()} connected to notifications")
    
    async def handle_disconnect(self, close_code):
        """Handle notification disconnection"""
        # Only proceed if room_group_name was set (i.e., connection was successful)
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def emergency_notification(self, event):
        """Send emergency notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'emergency_notification',
            'title': event['title'],
            'message': event['message'],
            'priority': 'emergency',
            'timestamp': event['timestamp'],
            'conversation_id': event.get('conversation_id'),
            'actions': event.get('actions', [])
        }))
    
    async def mention_notification(self, event):
        """Send mention notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'mention',
            'message': event['message'],
            'conversation_id': event['conversation_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp']
        }))
    
    async def system_notification(self, event):
        """Send system notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'system_notification',
            'title': event['title'],
            'message': event['message'],
            'category': event.get('category', 'info'),
            'timestamp': event['timestamp']
        }))