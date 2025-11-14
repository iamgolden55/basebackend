"""
Test WebSocket functionality for healthcare messaging system

This command tests the real-time messaging infrastructure including:
- WebSocket connections
- Redis channel layer
- Message broadcasting
- Auto-scaling storage
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from api.models import CustomUser, Hospital
from api.models.messaging import Conversation, get_auto_scaling_storage
import json
import time

class Command(BaseCommand):
    help = 'Test WebSocket messaging infrastructure'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-type',
            type=str,
            default='all',
            choices=['all', 'channels', 'storage', 'broadcast'],
            help='Type of test to run'
        )
        parser.add_argument(
            '--messages',
            type=int,
            default=10,
            help='Number of test messages to send'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧪 Testing WebSocket Infrastructure\n')
        )
        
        test_type = options['test_type']
        
        if test_type in ['all', 'channels']:
            self.test_channel_layer()
        
        if test_type in ['all', 'storage']:
            self.test_auto_scaling_storage()
        
        if test_type in ['all', 'broadcast']:
            self.test_message_broadcasting(options['messages'])
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ All tests completed!')
        )
    
    def test_channel_layer(self):
        """Test Redis channel layer connectivity"""
        self.stdout.write("🔗 Testing Channel Layer (Redis)...")
        
        try:
            channel_layer = get_channel_layer()
            
            # Test basic channel operations
            test_channel = 'test_channel'
            test_message = {
                'type': 'test_message',
                'data': 'Hello WebSocket!',
                'timestamp': timezone.now().isoformat()
            }
            
            # Send message to channel
            async_to_sync(channel_layer.send)(test_channel, test_message)
            
            # Try to receive message
            received = async_to_sync(channel_layer.receive)(test_channel)
            
            if received:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ Channel layer working: {received['data']}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("  ❌ No message received from channel")
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ❌ Channel layer error: {e}")
            )
            self.stdout.write(
                self.style.WARNING("  💡 Make sure Redis is running: redis-server")
            )
    
    def test_auto_scaling_storage(self):
        """Test auto-scaling message storage"""
        self.stdout.write("\n📦 Testing Auto-Scaling Storage...")
        
        try:
            storage = get_auto_scaling_storage()
            
            # Get storage info
            info = storage.get_storage_info()
            
            self.stdout.write(f"  📊 Current Strategy: {info['current_strategy'].upper()}")
            self.stdout.write(f"  📈 Total Messages: {info['metrics']['message_count']:,}")
            self.stdout.write(f"  ⚡ DB Response Time: {info['metrics']['db_response_time']:.1f}ms")
            
            # Create test data if needed
            test_data = self.create_test_data()
            if not test_data:
                self.stdout.write(
                    self.style.ERROR("  ❌ Could not create test data for storage test")
                )
                return
            
            # Test message storage
            test_message_data = {
                'conversation_id': str(test_data['conversation'].id),
                'sender_id': str(test_data['users'][0].id),
                'content': 'Test message for WebSocket infrastructure',
                'message_type': 'text',
                'priority_level': 'routine',
                'created_at': timezone.now(),
            }
            
            message_id = storage.store_message(test_message_data)
            
            if message_id:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ Message stored with ID: {message_id[:8]}...")
                )
                
                # Test message retrieval
                retrieved = storage.retrieve_message(message_id)
                if retrieved:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✅ Message retrieved: {retrieved.get('content', '')[:30]}...")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING("  ⚠️ Message stored but couldn't retrieve")
                    )
            else:
                self.stdout.write(
                    self.style.ERROR("  ❌ Failed to store test message")
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ❌ Storage error: {e}")
            )
    
    def test_message_broadcasting(self, message_count):
        """Test message broadcasting through channels"""
        self.stdout.write(f"\n📡 Testing Message Broadcasting ({message_count} messages)...")
        
        try:
            channel_layer = get_channel_layer()
            
            # Create test conversation room
            room_name = 'chat_test_conversation'
            
            for i in range(message_count):
                # Create test message
                test_message = {
                    'type': 'chat_message',
                    'message': {
                        'id': f'test_msg_{i}',
                        'content': f'Test broadcast message {i + 1}',
                        'sender': {
                            'id': 'test_user',
                            'name': 'Test User',
                            'role': 'hospital_admin'
                        },
                        'timestamp': timezone.now().isoformat(),
                        'message_type': 'text',
                        'priority_level': 'routine'
                    },
                    'sender_id': 'test_user'
                }
                
                # Broadcast to room
                async_to_sync(channel_layer.group_send)(room_name, test_message)
                
                if (i + 1) % 5 == 0:
                    self.stdout.write(f"  📤 Sent {i + 1}/{message_count} messages")
                
                # Small delay to avoid overwhelming
                time.sleep(0.1)
            
            self.stdout.write(
                self.style.SUCCESS(f"  ✅ Successfully broadcasted {message_count} messages")
            )
            
            # Test typing indicators
            typing_message = {
                'type': 'typing_status',
                'user_id': 'test_user',
                'user_name': 'Test User',
                'is_typing': True,
                'timestamp': timezone.now().isoformat()
            }
            
            async_to_sync(channel_layer.group_send)(
                f'typing_test_conversation', 
                typing_message
            )
            
            self.stdout.write(
                self.style.SUCCESS("  ✅ Typing indicator test sent")
            )
            
            # Test presence update
            presence_message = {
                'type': 'presence_update',
                'user_id': 'test_user',
                'status': 'online',
                'last_seen': timezone.now().isoformat()
            }
            
            async_to_sync(channel_layer.group_send)(
                'presence_test_user',
                presence_message
            )
            
            self.stdout.write(
                self.style.SUCCESS("  ✅ Presence update test sent")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ❌ Broadcasting error: {e}")
            )
    
    def create_test_data(self):
        """Create test users and conversations for WebSocket testing"""
        self.stdout.write("\n👥 Creating test data...")
        
        try:
            # Create test hospital
            hospital, created = Hospital.objects.get_or_create(
                name='Test Hospital for WebSocket',
                defaults={
                    'address': 'Test Address',
                    'city': 'Test City',
                    'state': 'Test State',
                    'country': 'NG',
                    'phone': '+2347000000000',
                    'email': 'test@hospital.com',
                    'hospital_type': 'public',
                    'is_verified': True
                }
            )
            
            if created:
                self.stdout.write(f"  ✅ Created test hospital: {hospital.name}")
            
            # Create test users
            test_users = []
            for i in range(2):
                user, created = CustomUser.objects.get_or_create(
                    email=f'testuser{i}@hospital.com',
                    defaults={
                        'first_name': f'Test{i}',
                        'last_name': f'User{i}',
                        'role': 'hospital_admin',
                        'is_active': True,
                    }
                )
                test_users.append(user)
                if created:
                    self.stdout.write(f"  ✅ Created test user: {user.get_full_name()}")
            
            # Create test conversation
            conversation, created = Conversation.objects.get_or_create(
                title='Test WebSocket Conversation',
                defaults={
                    'conversation_type': 'group',
                    'priority_level': 'routine',
                    'hospital_context': hospital,
                    'created_by': test_users[0]
                }
            )
            
            if created:
                # Add participants
                for user in test_users:
                    conversation.add_participant(user)
                
                self.stdout.write(f"  ✅ Created test conversation: {conversation.title}")
            
            return {
                'hospital': hospital,
                'users': test_users,
                'conversation': conversation
            }
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ❌ Error creating test data: {e}")
            )
            return None