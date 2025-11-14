"""
Demo script to show auto-scaling message storage in action

This command demonstrates how the system automatically scales
from Local → Hybrid → Firebase based on message volume and performance.

Usage: python manage.py demo_autoscaling
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models.messaging import get_auto_scaling_storage, MessageAuditLog
from api.models import CustomUser, Hospital
import time
import random


class Command(BaseCommand):
    help = 'Demonstrate auto-scaling message storage system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--messages',
            type=int,
            default=1000,
            help='Number of test messages to create'
        )
        parser.add_argument(
            '--show-scaling',
            action='store_true',
            help='Show scaling decisions in real-time'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset storage strategy to local'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Auto-Scaling Message Storage Demo\n')
        )
        
        # Get auto-scaling storage instance
        storage = get_auto_scaling_storage()
        
        if options['reset']:
            self._reset_storage_strategy(storage)
            return
        
        # Show initial state
        self._show_storage_info(storage)
        
        # Create test users and conversations
        users = self._create_test_users()
        conversations = self._create_test_conversations(users)
        
        # Simulate message load
        message_count = options['messages']
        self._simulate_message_load(storage, users, conversations, message_count)
        
        # Show final state
        self._show_storage_info(storage)
        
        # Show scaling history
        self._show_scaling_history()
    
    def _show_storage_info(self, storage):
        """Display current storage information"""
        info = storage.get_storage_info()
        
        self.stdout.write(f"\n📊 Storage Information:")
        self.stdout.write(f"Current Strategy: {info['current_strategy'].upper()}")
        
        metrics = info['metrics']
        self.stdout.write(f"\n📈 Current Metrics:")
        self.stdout.write(f"  • Total Messages: {metrics['message_count']:,}")
        self.stdout.write(f"  • DB Response Time: {metrics['db_response_time']:.1f}ms")
        self.stdout.write(f"  • DB Size: {metrics['db_size_gb']:.2f} GB")
        self.stdout.write(f"  • Concurrent Users: {metrics['concurrent_users']}")
        self.stdout.write(f"  • Messages/Hour: {metrics['messages_per_hour']}")
        
        thresholds = info['thresholds']
        self.stdout.write(f"\n🎯 Scaling Thresholds:")
        self.stdout.write(f"  • Hybrid Threshold: {thresholds['hybrid_threshold']:,} messages")
        self.stdout.write(f"  • Firebase Threshold: {thresholds['firebase_threshold']:,} messages")
        self.stdout.write(f"  • Max Response Time: {thresholds['max_response_time']}ms")
        self.stdout.write(f"  • Max DB Size: {thresholds['max_db_size']} GB")
        
        recommendations = info['recommendations']
        if recommendations:
            self.stdout.write(f"\n💡 Recommendations:")
            for rec in recommendations:
                self.stdout.write(f"  • {rec}")
        
        # Calculate progress to next threshold
        current_count = metrics['message_count']
        if info['current_strategy'] == 'local':
            next_threshold = thresholds['hybrid_threshold']
            progress = (current_count / next_threshold) * 100
            self.stdout.write(f"\n⏳ Progress to Hybrid: {progress:.1f}%")
        elif info['current_strategy'] == 'hybrid':
            next_threshold = thresholds['firebase_threshold']
            progress = (current_count / next_threshold) * 100
            self.stdout.write(f"\n⏳ Progress to Firebase: {progress:.1f}%")
    
    def _create_test_users(self):
        """Create test users for the demo"""
        self.stdout.write("\n👥 Creating test users...")
        
        users = []
        for i in range(5):
            user, created = CustomUser.objects.get_or_create(
                email=f'demo_user_{i}@hospital.com',
                defaults={
                    'first_name': f'Doctor{i}',
                    'last_name': f'Test{i}',
                    'role': 'hospital_admin',
                    'is_active': True,
                }
            )
            users.append(user)
            if created:
                self.stdout.write(f"  ✓ Created {user.get_full_name()}")
        
        return users
    
    def _create_test_conversations(self, users):
        """Create test conversations"""
        from api.models.messaging import Conversation
        
        self.stdout.write("\n💬 Creating test conversations...")
        
        conversations = []
        conversation_types = [
            ('direct', 'Direct Message'),
            ('group', 'Emergency Team'),
            ('department', 'ICU Department'),
        ]
        
        for i, (conv_type, title) in enumerate(conversation_types):
            conversation, created = Conversation.objects.get_or_create(
                title=f'Demo {title} {i}',
                defaults={
                    'conversation_type': conv_type,
                    'priority_level': 'routine',
                    'created_by': users[0],
                }
            )
            
            # Add participants
            for user in users[:3]:  # Add first 3 users to each conversation
                conversation.add_participant(user)
            
            conversations.append(conversation)
            if created:
                self.stdout.write(f"  ✓ Created {conversation}")
        
        return conversations
    
    def _simulate_message_load(self, storage, users, conversations, message_count):
        """Simulate realistic message load"""
        self.stdout.write(f"\n📨 Simulating {message_count:,} messages...")
        
        message_types = ['text', 'image', 'document', 'voice']
        priorities = ['routine', 'urgent', 'emergency']
        
        batch_size = 100
        batches = message_count // batch_size
        
        for batch in range(batches):
            self.stdout.write(f"  📦 Batch {batch + 1}/{batches} ({batch_size} messages)")
            
            for i in range(batch_size):
                # Random message data
                sender = random.choice(users)
                conversation = random.choice(conversations)
                message_type = random.choice(message_types)
                priority = random.choice(priorities)
                
                # Create message content based on type
                if message_type == 'text':
                    content = self._generate_random_medical_message()
                else:
                    content = f"[{message_type.upper()}] Medical {message_type} file"
                
                # Message data
                message_data = {
                    'conversation_id': str(conversation.id),
                    'sender_id': str(sender.id),
                    'content': content,
                    'message_type': message_type,
                    'priority_level': priority,
                    'created_at': timezone.now(),
                }
                
                try:
                    # Store message (this will trigger auto-scaling checks)
                    message_id = storage.store_message(message_data)
                    
                    # Simulate some processing time
                    time.sleep(0.001)  # 1ms per message
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"    ❌ Failed to store message: {e}")
                    )
            
            # Show progress every few batches
            if (batch + 1) % 5 == 0:
                current_info = storage.get_storage_info()
                current_strategy = current_info['current_strategy']
                current_count = current_info['metrics']['message_count']
                
                self.stdout.write(
                    f"    📊 Progress: {current_count:,} messages, Strategy: {current_strategy.upper()}"
                )
        
        self.stdout.write(self.style.SUCCESS(f"  ✅ Completed {message_count:,} messages"))
    
    def _generate_random_medical_message(self):
        """Generate realistic medical message content"""
        templates = [
            "Patient {hpn} requires immediate attention in {department}",
            "Lab results for {hpn} are ready for review",
            "Surgery scheduled for {hpn} at {time}",
            "Medication dosage updated for patient {hpn}",
            "Emergency admission: {hpn} - {condition}",
            "Discharge planning meeting for {hpn} at {time}",
            "CT scan results abnormal for patient {hpn}",
            "Blood pressure monitoring required for {hpn}",
        ]
        
        template = random.choice(templates)
        
        replacements = {
            '{hpn}': f"HPN{random.randint(100000, 999999)}",
            '{department}': random.choice(['ICU', 'Emergency', 'Surgery', 'Cardiology']),
            '{time}': f"{random.randint(8, 17)}:00",
            '{condition}': random.choice(['chest pain', 'shortness of breath', 'severe headache']),
        }
        
        message = template
        for placeholder, value in replacements.items():
            message = message.replace(placeholder, value)
        
        return message
    
    def _show_scaling_history(self):
        """Show history of storage scaling decisions"""
        self.stdout.write(f"\n📋 Scaling History:")
        
        scaling_logs = MessageAuditLog.objects.filter(
            action='storage_strategy_switch'
        ).order_by('-timestamp')[:10]
        
        if not scaling_logs.exists():
            self.stdout.write("  No scaling events recorded yet")
            return
        
        for log in scaling_logs:
            details = log.details
            from_strategy = details.get('from_strategy', 'unknown')
            to_strategy = details.get('to_strategy', 'unknown')
            timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            metrics = details.get('metrics', {})
            message_count = metrics.get('message_count', 0)
            
            self.stdout.write(
                f"  📈 {timestamp}: {from_strategy.upper()} → {to_strategy.upper()} "
                f"({message_count:,} messages)"
            )
    
    def _reset_storage_strategy(self, storage):
        """Reset storage strategy to local for testing"""
        self.stdout.write("🔄 Resetting storage strategy to LOCAL...")
        
        # Force switch to local strategy
        storage._switch_to_strategy('local')
        
        self.stdout.write(
            self.style.SUCCESS("✅ Storage strategy reset to LOCAL")
        )
        
        # Show current state
        self._show_storage_info(storage)