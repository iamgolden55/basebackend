"""
Auto-Scaling Message Storage System for Healthcare Messaging

This system automatically detects when to upgrade storage strategies based on:
1. Message volume thresholds
2. Database performance metrics  
3. Storage size limits
4. Concurrent user load

It seamlessly migrates from Local → Hybrid → Firebase without downtime.
"""

import logging
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from typing import Dict, List, Optional, Any, Tuple
import threading

from .message_storage_strategy import (
    MessageStorageStrategy,
    LocalDatabaseStrategy, 
    HybridStrategy,
    FirebaseStrategy
)

logger = logging.getLogger('messaging.autoscaling')


class StorageMetrics:
    """Track storage performance and usage metrics"""
    
    @staticmethod
    def get_total_message_count() -> int:
        """Get total number of messages in the system"""
        try:
            from .message import Message
            count = cache.get('message_total_count')
            if count is None:
                count = Message.objects.count()
                # Cache for 5 minutes to avoid constant DB hits
                cache.set('message_total_count', count, 300)
            return count
        except Exception as e:
            logger.error(f"Failed to get message count: {e}")
            return 0
    
    @staticmethod
    def get_database_response_time() -> float:
        """Measure average database response time in milliseconds"""
        try:
            start_time = time.time()
            
            # Test query performance
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM messaging_message WHERE created_at > %s", 
                             [timezone.now() - timedelta(hours=1)])
                cursor.fetchone()
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Cache the result
            cache.set('db_response_time', response_time, 60)  # Cache for 1 minute
            return response_time
        except Exception as e:
            logger.error(f"Failed to measure DB response time: {e}")
            return 0.0
    
    @staticmethod
    def get_database_size_gb() -> float:
        """Get database size in GB"""
        try:
            size_gb = cache.get('db_size_gb')
            if size_gb is None:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT pg_size_pretty(pg_total_relation_size('messaging_message')) as size,
                               pg_total_relation_size('messaging_message') as size_bytes
                    """)
                    result = cursor.fetchone()
                    if result:
                        size_gb = result[1] / (1024**3)  # Convert bytes to GB
                    else:
                        size_gb = 0.0
                
                # Cache for 30 minutes
                cache.set('db_size_gb', size_gb, 1800)
            
            return size_gb
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return 0.0
    
    @staticmethod
    def get_concurrent_users() -> int:
        """Get number of active users in last 5 minutes"""
        try:
            from .message_participant import MessageParticipant
            
            active_count = cache.get('concurrent_users')
            if active_count is None:
                cutoff_time = timezone.now() - timedelta(minutes=5)
                active_count = MessageParticipant.objects.filter(
                    last_seen_at__gte=cutoff_time,
                    is_active=True
                ).values('user').distinct().count()
                
                # Cache for 1 minute
                cache.set('concurrent_users', active_count, 60)
            
            return active_count
        except Exception as e:
            logger.error(f"Failed to get concurrent users: {e}")
            return 0
    
    @staticmethod
    def get_messages_per_hour() -> int:
        """Get message rate in the last hour"""
        try:
            from .message import Message
            
            rate = cache.get('messages_per_hour')
            if rate is None:
                cutoff_time = timezone.now() - timedelta(hours=1)
                rate = Message.objects.filter(
                    created_at__gte=cutoff_time,
                    is_deleted=False
                ).count()
                
                # Cache for 5 minutes
                cache.set('messages_per_hour', rate, 300)
            
            return rate
        except Exception as e:
            logger.error(f"Failed to get message rate: {e}")
            return 0


class StorageThresholds:
    """Define thresholds for auto-scaling decisions"""
    
    # Message count thresholds
    HYBRID_MESSAGE_THRESHOLD = getattr(settings, 'AUTO_SCALE_HYBRID_THRESHOLD', 5_000_000)  # 5M
    FIREBASE_MESSAGE_THRESHOLD = getattr(settings, 'AUTO_SCALE_FIREBASE_THRESHOLD', 50_000_000)  # 50M
    
    # Performance thresholds
    MAX_DB_RESPONSE_TIME_MS = getattr(settings, 'AUTO_SCALE_MAX_RESPONSE_TIME', 500)  # 500ms
    MAX_DB_SIZE_GB = getattr(settings, 'AUTO_SCALE_MAX_DB_SIZE', 100)  # 100GB
    MAX_CONCURRENT_USERS = getattr(settings, 'AUTO_SCALE_MAX_CONCURRENT_USERS', 1000)
    MAX_MESSAGES_PER_HOUR = getattr(settings, 'AUTO_SCALE_MAX_MESSAGE_RATE', 10000)
    
    # Safety thresholds (when to force upgrade)
    FORCE_HYBRID_THRESHOLD = HYBRID_MESSAGE_THRESHOLD * 1.2  # 6M messages
    FORCE_FIREBASE_THRESHOLD = FIREBASE_MESSAGE_THRESHOLD * 1.2  # 60M messages


class AutoScalingMessageStorage(MessageStorageStrategy):
    """
    Auto-scaling message storage that intelligently switches between strategies
    """
    
    def __init__(self):
        self.current_strategy = None
        self.strategy_type = None
        self._lock = threading.Lock()
        self._initialize_strategy()
    
    def _initialize_strategy(self):
        """Initialize with the best strategy for current state"""
        with self._lock:
            best_strategy_type = self._determine_best_strategy()
            self._switch_to_strategy(best_strategy_type)
            logger.info(f"Initialized auto-scaling storage with strategy: {best_strategy_type}")
    
    def _determine_best_strategy(self) -> str:
        """Determine the best storage strategy based on current metrics"""
        metrics = self._get_current_metrics()
        
        # Log current metrics for monitoring
        logger.info(f"Storage metrics: {metrics}")
        
        # Check if we need Firebase (highest tier)
        if self._should_use_firebase(metrics):
            return 'firebase'
        
        # Check if we need Hybrid (middle tier)
        elif self._should_use_hybrid(metrics):
            return 'hybrid'
        
        # Default to local (lowest tier)
        else:
            return 'local'
    
    def _should_use_firebase(self, metrics: Dict) -> bool:
        """Check if Firebase strategy is needed"""
        conditions = [
            metrics['message_count'] >= StorageThresholds.FIREBASE_MESSAGE_THRESHOLD,
            metrics['db_size_gb'] >= StorageThresholds.MAX_DB_SIZE_GB * 2,  # 200GB
            metrics['concurrent_users'] >= StorageThresholds.MAX_CONCURRENT_USERS * 2,  # 2000 users
            metrics['messages_per_hour'] >= StorageThresholds.MAX_MESSAGES_PER_HOUR * 3,  # 30k/hour
            metrics['message_count'] >= StorageThresholds.FORCE_FIREBASE_THRESHOLD,  # Force threshold
        ]
        
        # Need Firebase if any condition is met
        return any(conditions)
    
    def _should_use_hybrid(self, metrics: Dict) -> bool:
        """Check if Hybrid strategy is needed"""
        conditions = [
            metrics['message_count'] >= StorageThresholds.HYBRID_MESSAGE_THRESHOLD,
            metrics['db_response_time'] >= StorageThresholds.MAX_DB_RESPONSE_TIME_MS,
            metrics['db_size_gb'] >= StorageThresholds.MAX_DB_SIZE_GB,
            metrics['concurrent_users'] >= StorageThresholds.MAX_CONCURRENT_USERS,
            metrics['messages_per_hour'] >= StorageThresholds.MAX_MESSAGES_PER_HOUR,
            metrics['message_count'] >= StorageThresholds.FORCE_HYBRID_THRESHOLD,  # Force threshold
        ]
        
        # Need Hybrid if any condition is met
        return any(conditions)
    
    def _get_current_metrics(self) -> Dict:
        """Get current system metrics"""
        return {
            'message_count': StorageMetrics.get_total_message_count(),
            'db_response_time': StorageMetrics.get_database_response_time(),
            'db_size_gb': StorageMetrics.get_database_size_gb(),
            'concurrent_users': StorageMetrics.get_concurrent_users(),
            'messages_per_hour': StorageMetrics.get_messages_per_hour(),
            'timestamp': timezone.now().isoformat(),
        }
    
    def _switch_to_strategy(self, strategy_type: str):
        """Switch to a new storage strategy"""
        if strategy_type == self.strategy_type:
            return  # Already using this strategy
        
        old_strategy = self.strategy_type
        
        # Create new strategy instance
        if strategy_type == 'firebase':
            self.current_strategy = FirebaseStrategy()
        elif strategy_type == 'hybrid':
            self.current_strategy = HybridStrategy()
        else:
            self.current_strategy = LocalDatabaseStrategy()
        
        self.strategy_type = strategy_type
        
        # Log the switch
        logger.warning(f"AUTO-SCALED: Switched from {old_strategy} to {strategy_type}")
        
        # Trigger migration if needed
        if old_strategy and old_strategy != strategy_type:
            self._trigger_background_migration(old_strategy, strategy_type)
        
        # Update metrics
        self._record_strategy_switch(old_strategy, strategy_type)
    
    def _trigger_background_migration(self, from_strategy: str, to_strategy: str):
        """Trigger background migration of data"""
        try:
            from api.tasks.messaging import migrate_message_storage
            migrate_message_storage.delay(from_strategy, to_strategy)
            logger.info(f"Triggered background migration from {from_strategy} to {to_strategy}")
        except ImportError:
            logger.warning("Celery not available, skipping background migration")
        except Exception as e:
            logger.error(f"Failed to trigger migration: {e}")
    
    def _record_strategy_switch(self, from_strategy: str, to_strategy: str):
        """Record strategy switch for monitoring"""
        try:
            from .message_audit_log import MessageAuditLog
            
            MessageAuditLog.objects.create(
                action='storage_strategy_switch',
                details={
                    'from_strategy': from_strategy,
                    'to_strategy': to_strategy,
                    'metrics': self._get_current_metrics(),
                    'automatic': True
                },
                user=None,  # System action
                conversation=None
            )
        except Exception as e:
            logger.error(f"Failed to record strategy switch: {e}")
    
    def _check_and_auto_scale(self):
        """Check if auto-scaling is needed and perform it"""
        with self._lock:
            # Only check every 5 minutes to avoid constant switching
            last_check = cache.get('last_autoscale_check')
            now = time.time()
            
            if last_check and (now - last_check) < 300:  # 5 minutes
                return
            
            cache.set('last_autoscale_check', now, 300)
            
            # Determine if we need to switch
            best_strategy = self._determine_best_strategy()
            
            if best_strategy != self.strategy_type:
                logger.info(f"Auto-scaling triggered: {self.strategy_type} → {best_strategy}")
                self._switch_to_strategy(best_strategy)
    
    # Implement MessageStorageStrategy interface
    
    def store_message(self, message_data: Dict) -> str:
        """Store message and check for auto-scaling"""
        # Check if we need to auto-scale (on every 100th message to avoid overhead)
        message_count = StorageMetrics.get_total_message_count()
        if message_count % 100 == 0:  # Check every 100 messages
            self._check_and_auto_scale()
        
        # Store the message using current strategy
        try:
            return self.current_strategy.store_message(message_data)
        except Exception as e:
            logger.error(f"Failed to store message with {self.strategy_type} strategy: {e}")
            
            # Try to auto-upgrade on failure
            if self.strategy_type == 'local':
                logger.warning("Local storage failed, auto-upgrading to hybrid")
                self._switch_to_strategy('hybrid')
                return self.current_strategy.store_message(message_data)
            elif self.strategy_type == 'hybrid':
                logger.warning("Hybrid storage failed, auto-upgrading to firebase")
                self._switch_to_strategy('firebase')
                return self.current_strategy.store_message(message_data)
            else:
                raise
    
    def retrieve_message(self, message_id: str) -> Optional[Dict]:
        """Retrieve message using current strategy"""
        return self.current_strategy.retrieve_message(message_id)
    
    def retrieve_conversation_messages(self, conversation_id: str, limit: int = 50, before_timestamp: Optional[datetime] = None) -> List[Dict]:
        """Retrieve conversation messages using current strategy"""
        return self.current_strategy.retrieve_conversation_messages(
            conversation_id, limit, before_timestamp
        )
    
    def delete_message(self, message_id: str) -> bool:
        """Delete message using current strategy"""
        if hasattr(self.current_strategy, 'delete_message'):
            return self.current_strategy.delete_message(message_id)
        return False
    
    def search_messages(self, query: str, conversation_id: Optional[str] = None) -> List[Dict]:
        """Search messages using current strategy"""
        if hasattr(self.current_strategy, 'search_messages'):
            return self.current_strategy.search_messages(query, conversation_id)
        return []
    
    def get_storage_info(self) -> Dict:
        """Get information about current storage strategy and metrics"""
        return {
            'current_strategy': self.strategy_type,
            'metrics': self._get_current_metrics(),
            'thresholds': {
                'hybrid_threshold': StorageThresholds.HYBRID_MESSAGE_THRESHOLD,
                'firebase_threshold': StorageThresholds.FIREBASE_MESSAGE_THRESHOLD,
                'max_response_time': StorageThresholds.MAX_DB_RESPONSE_TIME_MS,
                'max_db_size': StorageThresholds.MAX_DB_SIZE_GB,
                'max_concurrent_users': StorageThresholds.MAX_CONCURRENT_USERS,
            },
            'recommendations': self._get_scaling_recommendations()
        }
    
    def _get_scaling_recommendations(self) -> List[str]:
        """Get recommendations for manual scaling"""
        metrics = self._get_current_metrics()
        recommendations = []
        
        if metrics['message_count'] > StorageThresholds.HYBRID_MESSAGE_THRESHOLD * 0.8:
            recommendations.append("Consider preparing for Hybrid storage migration")
        
        if metrics['message_count'] > StorageThresholds.FIREBASE_MESSAGE_THRESHOLD * 0.8:
            recommendations.append("Consider preparing for Firebase storage migration")
        
        if metrics['db_response_time'] > StorageThresholds.MAX_DB_RESPONSE_TIME_MS * 0.8:
            recommendations.append("Database response time is getting high")
        
        if metrics['concurrent_users'] > StorageThresholds.MAX_CONCURRENT_USERS * 0.8:
            recommendations.append("Concurrent user count is approaching limits")
        
        return recommendations


# Factory function for getting the auto-scaling storage
def get_auto_scaling_storage() -> AutoScalingMessageStorage:
    """Get the auto-scaling message storage instance"""
    # Use singleton pattern to ensure one instance across the application
    if not hasattr(get_auto_scaling_storage, '_instance'):
        get_auto_scaling_storage._instance = AutoScalingMessageStorage()
    
    return get_auto_scaling_storage._instance