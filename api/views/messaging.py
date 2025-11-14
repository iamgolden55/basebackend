"""
REST API views for healthcare messaging system

This module provides RESTful endpoints for the WhatsApp-style messaging system,
integrating with the auto-scaling storage and WebSocket infrastructure.
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Max
from datetime import datetime, timedelta
import logging

from api.models import CustomUser, Hospital
from api.models.messaging import (
    Conversation, MessageParticipant, MessageAuditLog,
    get_auto_scaling_storage
)
from api.utils.messaging_utils import (
    MessagingNotifier, MessageProcessor, ConversationUtils
)

logger = logging.getLogger('messaging.api')


class MessagePagination(PageNumberPagination):
    """Custom pagination for messages"""
    page_size = 50
    page_size_query_param = 'limit'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_conversations(request):
    """
    Get list of conversations for the authenticated user
    
    Query parameters:
    - search: Search conversations by title
    - type: Filter by conversation type (direct, group, emergency, department)
    - hospital: Filter by hospital context
    - limit: Number of conversations per page (default 20)
    """
    try:
        user = request.user
        
        # Base queryset - conversations where user is a participant
        conversations_qs = Conversation.objects.filter(
            participants__user=user,
            participants__is_active=True
        ).distinct().select_related(
            'created_by', 
            'hospital_context'
        ).prefetch_related(
            'participants__user'
        ).annotate(
            active_participant_count=Count('participants', filter=Q(participants__is_active=True))
        ).order_by('-last_message_at', '-created_at')
        
        # Apply filters
        search = request.GET.get('search')
        if search:
            conversations_qs = conversations_qs.filter(
                Q(title__icontains=search) | 
                Q(department__icontains=search)
            )
        
        conversation_type = request.GET.get('type')
        if conversation_type:
            conversations_qs = conversations_qs.filter(conversation_type=conversation_type)
        
        hospital_id = request.GET.get('hospital')
        if hospital_id:
            conversations_qs = conversations_qs.filter(hospital_context_id=hospital_id)
        
        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get('limit', 20))
        page = paginator.paginate_queryset(conversations_qs, request)
        
        # Serialize conversation data
        conversations_data = []
        for conversation in page:
            # Get user's participation info
            participant = MessageParticipant.objects.get(
                conversation=conversation,
                user=user
            )
            
            # Get last message from storage
            storage = get_auto_scaling_storage()
            recent_messages = storage.retrieve_conversation_messages(
                str(conversation.id), 
                limit=1
            )
            last_message = recent_messages[0] if recent_messages else None
            
            conversations_data.append({
                'id': str(conversation.id),
                'title': conversation.title,
                'conversation_type': conversation.conversation_type,
                'priority_level': conversation.priority_level,
                'participant_count': conversation.participant_count,
                'unread_count': participant.unread_count,
                'is_muted': participant.is_muted,
                'last_message': last_message,
                'last_message_time': conversation.last_message_at.isoformat() if conversation.last_message_at else None,
                'created_at': conversation.created_at.isoformat(),
                'hospital_context': {
                    'id': str(conversation.hospital_context.id),
                    'name': conversation.hospital_context.name
                } if conversation.hospital_context else None,
                'created_by': {
                    'id': str(conversation.created_by.id),
                    'name': conversation.created_by.get_full_name(),
                    'role': getattr(conversation.created_by, 'role', 'user')
                } if conversation.created_by else None
            })
        
        return paginator.get_paginated_response(conversations_data)
        
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return Response(
            {'error': 'Failed to retrieve conversations'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_conversation(request):
    """
    Create a new conversation
    
    Required fields:
    - title: Conversation title
    - conversation_type: Type (direct, group, emergency, department)
    - participant_ids: List of user IDs to add as participants
    
    Optional fields:
    - hospital_context_id: Hospital context
    - department: Department name
    - priority_level: Priority (routine, urgent, emergency)
    - initial_message: Initial message content
    """
    try:
        data = request.data
        user = request.user
        
        # Validate required fields
        title = data.get('title', '').strip()
        conversation_type = data.get('conversation_type')
        participant_ids = data.get('participant_ids', [])
        
        if not title:
            return Response(
                {'error': 'Title is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not conversation_type:
            return Response(
                {'error': 'Conversation type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If no participants specified, just include the creator
        if not participant_ids:
            participant_ids = [str(user.id)]
        
        # Validate participants exist
        participants = CustomUser.objects.filter(id__in=participant_ids)
        if participants.count() != len(participant_ids):
            return Response(
                {'error': 'One or more participant IDs are invalid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate hospital context if provided
        hospital_context = None
        hospital_context_id = data.get('hospital_context_id')
        if hospital_context_id:
            try:
                hospital_context = Hospital.objects.get(id=hospital_context_id)
            except Hospital.DoesNotExist:
                return Response(
                    {'error': 'Invalid hospital context ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        with transaction.atomic():
            # Create conversation
            conversation = Conversation.objects.create(
                title=title,
                conversation_type=conversation_type,
                priority_level=data.get('priority_level', 'routine'),
                hospital_context=hospital_context,
                department=data.get('department', ''),
                created_by=user
            )
            
            # Add creator as admin
            conversation.add_participant(user, role='admin')
            
            # Add other participants
            for participant in participants:
                if participant != user:  # Don't add creator twice
                    conversation.add_participant(participant, role='member')
            
            # Send initial message if provided
            initial_message = data.get('initial_message', '').strip()
            if initial_message:
                storage = get_auto_scaling_storage()
                message_data = {
                    'conversation_id': str(conversation.id),
                    'sender_id': str(user.id),
                    'content': initial_message,
                    'message_type': 'text',
                    'priority_level': conversation.priority_level,
                    'created_at': timezone.now(),
                }
                
                message_id = storage.store_message(message_data)
                
                # Broadcast to WebSocket if message created
                if message_id:
                    message_broadcast_data = {
                        'id': message_id,
                        'content': initial_message,
                        'message_type': 'text',
                        'sender': {
                            'id': str(user.id),
                            'name': user.get_full_name(),
                            'role': getattr(user, 'role', 'user')
                        },
                        'timestamp': timezone.now().isoformat(),
                        'status': 'sent'
                    }
                    
                    MessagingNotifier.broadcast_to_conversation(
                        str(conversation.id),
                        message_broadcast_data
                    )
                    
                    # Send email notification to participants for initial message
                    try:
                        from api.utils.email import send_message_notification_email
                        for participant in participants:
                            if participant != user:  # Don't email the sender
                                send_message_notification_email(
                                    recipient_email=participant.email,
                                    recipient_name=participant.get_full_name(),
                                    sender_name=user.get_full_name(),
                                    message_preview=MessageProcessor.format_message_preview(initial_message),
                                    conversation_title=conversation.title
                                )
                                logger.info(f"Email notification sent to {participant.email} for conversation creation")
                    except Exception as e:
                        logger.error(f"Failed to send email notifications for conversation creation: {e}")
            
            # Log conversation creation
            MessageAuditLog.log_action(
                action='conversation_created',
                user=user,
                conversation=conversation,
                details={
                    'conversation_type': conversation_type,
                    'participant_count': len(participant_ids) + 1,
                    'has_initial_message': bool(initial_message)
                }
            )
            
            return Response({
                'id': str(conversation.id),
                'title': conversation.title,
                'conversation_type': conversation.conversation_type,
                'participant_count': len(participant_ids) + 1,
                'created_at': conversation.created_at.isoformat(),
                'message': 'Conversation created successfully'
            }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        return Response(
            {'error': 'Failed to create conversation'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_messages(request, conversation_id):
    """
    Get messages for a specific conversation
    
    Query parameters:
    - limit: Number of messages per page (default 50, max 100)
    - before: ISO timestamp to get messages before this time
    - search: Search messages by content
    """
    try:
        user = request.user
        
        # Verify user has access to conversation
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            if not conversation.is_participant(user):
                return Response(
                    {'error': 'Access denied to this conversation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get query parameters
        limit = min(int(request.GET.get('limit', 50)), 100)
        before_param = request.GET.get('before')
        search_query = request.GET.get('search', '').strip()
        
        # Parse before timestamp
        before_timestamp = None
        if before_param:
            try:
                before_timestamp = datetime.fromisoformat(before_param.replace('Z', '+00:00'))
            except ValueError:
                return Response(
                    {'error': 'Invalid before timestamp format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get messages from storage
        storage = get_auto_scaling_storage()
        
        if search_query:
            # Search messages (if storage supports it)
            try:
                messages = storage.search_messages(search_query, conversation_id)
            except NotImplementedError:
                return Response(
                    {'error': 'Message search not supported with current storage'},
                    status=status.HTTP_501_NOT_IMPLEMENTED
                )
        else:
            # Get regular paginated messages
            messages = storage.retrieve_conversation_messages(
                conversation_id,
                limit=limit,
                before_timestamp=before_timestamp
            )
        
        # Process messages for response
        processed_messages = []
        for message in messages:
            # Sanitize content for security
            if message.get('content'):
                message['content'] = MessageProcessor.sanitize_message_content(
                    message['content']
                )
            
            processed_messages.append(message)
        
        # Update user's last read timestamp
        try:
            participant = MessageParticipant.objects.get(
                conversation_id=conversation_id,
                user=user
            )
            participant.update_last_read()
        except MessageParticipant.DoesNotExist:
            pass
        
        return Response({
            'messages': processed_messages,
            'conversation_id': conversation_id,
            'count': len(processed_messages),
            'has_more': len(processed_messages) == limit
        })
        
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return Response(
            {'error': 'Failed to retrieve messages'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_message(request, conversation_id):
    """
    Send a message to a conversation
    
    Required fields:
    - content: Message content
    
    Optional fields:
    - message_type: Type (text, image, file, location, etc.)
    - priority_level: Priority (routine, urgent, emergency)
    - reply_to_id: ID of message being replied to
    - patient_context_id: Patient HPN for medical context
    """
    try:
        user = request.user
        data = request.data
        
        # Verify user has access to conversation
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            if not conversation.is_participant(user):
                return Response(
                    {'error': 'Access denied to this conversation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate message content
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        
        if not content and message_type == 'text':
            return Response(
                {'error': 'Message content cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Detect emergency content
        priority_level = data.get('priority_level', 'routine')
        if MessageProcessor.detect_emergency_keywords(content):
            priority_level = 'emergency'
        
        # Extract mentions and patient references
        mentions = MessageProcessor.extract_mentions(content)
        patient_refs = MessageProcessor.extract_patient_references(content)
        
        # Sanitize content
        sanitized_content = MessageProcessor.sanitize_message_content(content)
        
        # Store message using auto-scaling storage
        storage = get_auto_scaling_storage()
        message_data = {
            'conversation_id': conversation_id,
            'sender_id': str(user.id),
            'content': sanitized_content,
            'message_type': message_type,
            'priority_level': priority_level,
            'created_at': timezone.now(),
        }
        
        # Add optional fields
        reply_to_id = data.get('reply_to_id')
        if reply_to_id:
            message_data['reply_to_id'] = reply_to_id
        
        patient_context_id = data.get('patient_context_id')
        if patient_context_id:
            message_data['patient_context_id'] = patient_context_id
        
        with transaction.atomic():
            # Store message
            message_id = storage.store_message(message_data)
            
            if not message_id:
                return Response(
                    {'error': 'Failed to store message'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Update conversation last message time
            conversation.update_last_message_time()
            
            # Update unread counts for other participants
            other_participants = MessageParticipant.objects.filter(
                conversation_id=conversation_id,
                is_active=True
            ).exclude(user=user)
            
            for participant in other_participants:
                participant.increment_unread_count()
        
        # Prepare message for broadcasting
        broadcast_message = {
            'id': message_id,
            'content': sanitized_content,
            'message_type': message_type,
            'priority_level': priority_level,
            'sender': {
                'id': str(user.id),
                'name': user.get_full_name(),
                'role': getattr(user, 'role', 'user')
            },
            'timestamp': timezone.now().isoformat(),
            'reply_to_id': reply_to_id,
            'patient_context_id': patient_context_id,
            'status': 'sent',
            'mentions': mentions,
            'patient_refs': patient_refs
        }
        
        # Broadcast to WebSocket
        MessagingNotifier.broadcast_to_conversation(conversation_id, broadcast_message)
        
        # Send email notification to other participants (if they're offline)
        try:
            from api.utils.email import send_message_notification_email
            for participant in other_participants:
                send_message_notification_email(
                    recipient_email=participant.user.email,
                    recipient_name=participant.user.get_full_name(),
                    sender_name=user.get_full_name(),
                    message_preview=MessageProcessor.format_message_preview(sanitized_content),
                    conversation_title=conversation.title
                )
        except Exception as e:
            logger.error(f"Failed to send email notifications: {e}")
        
        # Send mention notifications
        if mentions:
            for mention in mentions:
                try:
                    mentioned_user = CustomUser.objects.get(
                        Q(username=mention) | Q(email__icontains=mention)
                    )
                    if conversation.is_participant(mentioned_user):
                        MessagingNotifier.send_mention_notification(
                            str(mentioned_user.id),
                            conversation_id,
                            user.get_full_name(),
                            MessageProcessor.format_message_preview(content)
                        )
                except CustomUser.DoesNotExist:
                    pass
        
        # Handle emergency messages
        if priority_level == 'emergency':
            participant_ids = list(
                MessageParticipant.objects.filter(
                    conversation_id=conversation_id,
                    is_active=True
                ).exclude(user=user).values_list('user_id', flat=True)
            )
            
            MessagingNotifier.send_emergency_alert(
                user_ids=[str(uid) for uid in participant_ids],
                title=f"Emergency in {conversation.title}",
                message=MessageProcessor.format_message_preview(content),
                conversation_id=conversation_id
            )
        
        # Log message action
        MessageAuditLog.log_action(
            action='message_sent',
            user=user,
            conversation=conversation,
            details={
                'message_id': message_id,
                'message_type': message_type,
                'priority_level': priority_level,
                'has_mentions': bool(mentions),
                'has_patient_refs': bool(patient_refs)
            }
        )
        
        return Response({
            'message_id': message_id,
            'status': 'sent',
            'timestamp': timezone.now().isoformat(),
            'message': 'Message sent successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return Response(
            {'error': 'Failed to send message'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_conversation_participants(request, conversation_id):
    """Get participants of a conversation with their status"""
    try:
        user = request.user
        
        # Verify access
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            if not conversation.is_participant(user):
                return Response(
                    {'error': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get participants summary
        summary = ConversationUtils.get_conversation_participants_summary(conversation_id)
        
        return Response(summary)
        
    except Exception as e:
        logger.error(f"Error getting participants: {e}")
        return Response(
            {'error': 'Failed to retrieve participants'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_emergency_conversation(request):
    """
    Create an emergency conversation with automatic participant selection
    
    Required fields:
    - emergency_type: Type of emergency (cardiac, trauma, respiratory, etc.)
    - hospital_id: Hospital context
    - initial_message: Emergency description
    
    Optional fields:
    - patient_hpn: Patient HPN if applicable
    """
    try:
        user = request.user
        data = request.data
        
        emergency_type = data.get('emergency_type', '').strip()
        hospital_id = data.get('hospital_id')
        initial_message = data.get('initial_message', '').strip()
        
        if not all([emergency_type, hospital_id, initial_message]):
            return Response(
                {'error': 'Emergency type, hospital ID, and initial message are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get hospital
        try:
            hospital = Hospital.objects.get(id=hospital_id)
        except Hospital.DoesNotExist:
            return Response(
                {'error': 'Hospital not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create emergency conversation
        conversation_id = ConversationUtils.create_emergency_conversation(
            creator_user=user,
            hospital=hospital,
            emergency_type=emergency_type,
            initial_message=initial_message
        )
        
        if conversation_id:
            return Response({
                'conversation_id': conversation_id,
                'emergency_type': emergency_type,
                'message': 'Emergency conversation created and alerts sent'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': 'Failed to create emergency conversation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        logger.error(f"Error creating emergency conversation: {e}")
        return Response(
            {'error': 'Failed to create emergency conversation'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_storage_info(request):
    """Get information about current message storage strategy and metrics"""
    try:
        storage = get_auto_scaling_storage()
        info = storage.get_storage_info()
        
        return Response({
            'current_strategy': info['current_strategy'],
            'total_messages': info['metrics']['message_count'],
            'db_response_time': f"{info['metrics']['db_response_time']:.1f}ms",
            'concurrent_users': info['metrics']['concurrent_users'],
            'messages_per_hour': info['metrics']['messages_per_hour'],
            'last_updated': info['metrics']['timestamp']
        })
        
    except Exception as e:
        logger.error(f"Error getting storage info: {e}")
        return Response(
            {'error': 'Failed to retrieve storage information'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )