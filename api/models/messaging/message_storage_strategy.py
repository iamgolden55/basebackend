"""
Scalable Message Storage Strategy for Healthcare Messaging

This module provides a hybrid approach to message storage that can scale
from local database storage to cloud-based solutions like Firebase,
AWS DynamoDB, or Google Cloud Firestore while maintaining HIPAA compliance.

Strategy Options:
1. Local Database (PostgreSQL) - For small to medium scale
2. Hybrid (Local + Cloud) - For medium to large scale  
3. Full Cloud (Firebase/DynamoDB) - For massive scale

All options maintain end-to-end encryption and HIPAA compliance.
"""

from django.conf import settings
from django.core.cache import cache
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger('messaging.storage')


class MessageStorageStrategy:
    """
    Abstract base class for message storage strategies
    """
    
    def store_message(self, message_data: Dict) -> str:
        """Store a message and return message ID"""
        raise NotImplementedError
    
    def retrieve_message(self, message_id: str) -> Optional[Dict]:
        """Retrieve a message by ID"""
        raise NotImplementedError
    
    def retrieve_conversation_messages(self, conversation_id: str, limit: int = 50, before_timestamp: Optional[datetime] = None) -> List[Dict]:
        """Retrieve messages for a conversation"""
        raise NotImplementedError
    
    def delete_message(self, message_id: str) -> bool:
        """Delete a message"""
        raise NotImplementedError
    
    def search_messages(self, query: str, conversation_id: Optional[str] = None) -> List[Dict]:
        """Search messages by content"""
        raise NotImplementedError


class LocalDatabaseStrategy(MessageStorageStrategy):
    """
    Traditional Django ORM storage - good for up to ~10M messages
    """
    
    def store_message(self, message_data: Dict) -> str:
        from .message import Message
        from .conversation import Conversation
        from api.models import CustomUser
        
        # Extract content and prepare for encryption
        content = message_data.pop('content', '')
        
        # Get model instances from IDs
        conversation_id = message_data.pop('conversation_id')
        sender_id = message_data.pop('sender_id')
        
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            sender = CustomUser.objects.get(id=sender_id)
        except (Conversation.DoesNotExist, CustomUser.DoesNotExist) as e:
            raise ValueError(f"Invalid conversation or sender ID: {e}")
        
        # Create message instance
        message = Message(
            conversation=conversation,
            sender=sender,
            **message_data
        )
        message.set_content(content)  # This will encrypt the content
        message.save()
        
        return str(message.id)
    
    def retrieve_message(self, message_id: str) -> Optional[Dict]:
        from .message import Message
        
        try:
            message = Message.objects.get(id=message_id)
            return self._message_to_dict(message)
        except Message.DoesNotExist:
            return None
    
    def retrieve_conversation_messages(self, conversation_id: str, limit: int = 50, before_timestamp: Optional[datetime] = None) -> List[Dict]:
        from .message import Message
        
        queryset = Message.objects.filter(
            conversation_id=conversation_id,
            is_deleted=False
        ).order_by('-created_at')
        
        if before_timestamp:
            queryset = queryset.filter(created_at__lt=before_timestamp)
        
        messages = queryset[:limit]
        return [self._message_to_dict(msg) for msg in messages]
    
    def _message_to_dict(self, message) -> Dict:
        """Convert message model to dictionary"""
        return {
            'id': str(message.id),
            'conversation_id': str(message.conversation_id),
            'sender_id': str(message.sender_id),
            'content': message.get_content(),
            'message_type': message.message_type,
            'created_at': message.created_at.isoformat(),
            'status': message.status,
            'priority_level': message.priority_level,
            # Add other fields as needed
        }


class FirebaseStrategy(MessageStorageStrategy):
    """
    Firebase Firestore storage - can handle billions of messages
    Maintains HIPAA compliance with proper configuration
    """
    
    def __init__(self):
        self.db = self._get_firestore_client()
    
    def _get_firestore_client(self):
        """Initialize Firebase client with HIPAA-compliant configuration"""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            # Initialize Firebase with service account (HIPAA compliant)
            if not firebase_admin._apps:
                cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
                firebase_admin.initialize_app(cred, {
                    'projectId': settings.FIREBASE_PROJECT_ID,
                })
            
            return firestore.client()
        except ImportError:
            logger.error("Firebase admin SDK not installed. Install with: pip install firebase-admin")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def store_message(self, message_data: Dict) -> str:
        """Store message in Firestore with encryption"""
        try:
            # Encrypt sensitive data before storing
            encrypted_data = self._encrypt_message_data(message_data)
            
            # Store in Firestore
            doc_ref = self.db.collection('messages').document()
            doc_ref.set({
                **encrypted_data,
                'created_at': firestore.SERVER_TIMESTAMP,
                'conversation_id': message_data['conversation_id'],
                'sender_id': message_data['sender_id'],
                'message_type': message_data['message_type'],
                'priority_level': message_data.get('priority_level', 'routine'),
            })
            
            # Also store minimal metadata in local DB for indexing
            self._store_local_metadata(doc_ref.id, message_data)
            
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Failed to store message in Firebase: {e}")
            raise
    
    def retrieve_message(self, message_id: str) -> Optional[Dict]:
        """Retrieve message from Firestore"""
        try:
            doc = self.db.collection('messages').document(message_id).get()
            if doc.exists:
                data = doc.to_dict()
                return self._decrypt_message_data(data)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve message from Firebase: {e}")
            return None
    
    def retrieve_conversation_messages(self, conversation_id: str, limit: int = 50, before_timestamp: Optional[datetime] = None) -> List[Dict]:
        """Retrieve conversation messages from Firestore"""
        try:
            query = self.db.collection('messages')\
                          .where('conversation_id', '==', conversation_id)\
                          .order_by('created_at', direction=firestore.Query.DESCENDING)\
                          .limit(limit)
            
            if before_timestamp:
                query = query.where('created_at', '<', before_timestamp)
            
            docs = query.stream()
            messages = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                messages.append(self._decrypt_message_data(data))
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to retrieve conversation messages from Firebase: {e}")
            return []
    
    def _encrypt_message_data(self, data: Dict) -> Dict:
        """Encrypt sensitive message data"""
        from .message import Message
        
        # Create temporary message instance for encryption
        temp_message = Message()
        encrypted_content = temp_message._encrypt_content(data.get('content', ''))
        content_hash = temp_message._generate_content_hash(data.get('content', ''))
        
        return {
            'encrypted_content': encrypted_content,
            'content_hash': content_hash,
            'is_encrypted': True,
        }
    
    def _decrypt_message_data(self, data: Dict) -> Dict:
        """Decrypt message data"""
        from .message import Message
        
        if data.get('is_encrypted') and data.get('encrypted_content'):
            temp_message = Message()
            content = temp_message._decrypt_content(data['encrypted_content'])
            data['content'] = content
        
        return data
    
    def _store_local_metadata(self, firebase_id: str, message_data: Dict):
        """Store minimal metadata in local DB for fast queries"""
        from .message_metadata import MessageMetadata
        
        MessageMetadata.objects.create(
            firebase_id=firebase_id,
            conversation_id=message_data['conversation_id'],
            sender_id=message_data['sender_id'],
            message_type=message_data['message_type'],
            priority_level=message_data.get('priority_level', 'routine'),
            created_at=datetime.now()
        )


class HybridStrategy(MessageStorageStrategy):
    """
    Hybrid approach: Recent messages in local DB, older messages in cloud
    Best of both worlds - fast recent access, unlimited scale
    """
    
    def __init__(self):
        self.local_strategy = LocalDatabaseStrategy()
        self.cloud_strategy = FirebaseStrategy()
        self.cutoff_days = getattr(settings, 'MESSAGE_LOCAL_RETENTION_DAYS', 30)
    
    def store_message(self, message_data: Dict) -> str:
        """Store in local DB primarily, with cloud backup"""
        try:
            # Store in local DB first
            message_id = self.local_strategy.store_message(message_data)
            
            # Asynchronously backup to cloud (using Celery task)
            self._backup_to_cloud_async(message_id, message_data)
            
            return message_id
        except Exception as e:
            logger.error(f"Failed to store message in hybrid strategy: {e}")
            # Fallback to cloud only
            return self.cloud_strategy.store_message(message_data)
    
    def retrieve_message(self, message_id: str) -> Optional[Dict]:
        """Try local first, then cloud"""
        # Try local first
        message = self.local_strategy.retrieve_message(message_id)
        if message:
            return message
        
        # Fallback to cloud
        return self.cloud_strategy.retrieve_message(message_id)
    
    def retrieve_conversation_messages(self, conversation_id: str, limit: int = 50, before_timestamp: Optional[datetime] = None) -> List[Dict]:
        """Intelligently retrieve from local and cloud"""
        cutoff_date = datetime.now() - timedelta(days=self.cutoff_days)
        
        if not before_timestamp or before_timestamp > cutoff_date:
            # Recent messages - use local DB
            return self.local_strategy.retrieve_conversation_messages(
                conversation_id, limit, before_timestamp
            )
        else:
            # Older messages - use cloud storage
            return self.cloud_strategy.retrieve_conversation_messages(
                conversation_id, limit, before_timestamp
            )
    
    def _backup_to_cloud_async(self, message_id: str, message_data: Dict):
        """Asynchronously backup message to cloud storage"""
        try:
            from api.tasks.messaging import backup_message_to_cloud
            backup_message_to_cloud.delay(message_id, message_data)
        except ImportError:
            # Celery not available, backup synchronously
            logger.warning("Celery not available, backing up message synchronously")
            try:
                self.cloud_strategy.store_message(message_data)
            except Exception as e:
                logger.error(f"Failed to backup message to cloud: {e}")


def get_message_storage_strategy() -> MessageStorageStrategy:
    """
    Factory function to get the appropriate storage strategy based on settings
    """
    strategy_name = getattr(settings, 'MESSAGE_STORAGE_STRATEGY', 'local')
    
    if strategy_name == 'firebase':
        return FirebaseStrategy()
    elif strategy_name == 'hybrid':
        return HybridStrategy()
    else:
        return LocalDatabaseStrategy()


# Configuration examples for settings.py:

"""
# Local Database Only (default)
MESSAGE_STORAGE_STRATEGY = 'local'

# Firebase Cloud Storage
MESSAGE_STORAGE_STRATEGY = 'firebase'
FIREBASE_PROJECT_ID = 'your-hipaa-compliant-project'
FIREBASE_SERVICE_ACCOUNT_KEY = '/path/to/service-account-key.json'

# Hybrid (recommended for scaling)
MESSAGE_STORAGE_STRATEGY = 'hybrid'
MESSAGE_LOCAL_RETENTION_DAYS = 30  # Keep recent messages locally
FIREBASE_PROJECT_ID = 'your-hipaa-compliant-project'
FIREBASE_SERVICE_ACCOUNT_KEY = '/path/to/service-account-key.json'

# For HIPAA compliance with Firebase:
# 1. Use Firebase with BAA (Business Associate Agreement)
# 2. Enable VPC Service Controls
# 3. Use Customer-Managed Encryption Keys (CMEK)
# 4. Configure access controls and audit logging
# 5. Set up data residency controls
"""