import random
from django.core.management.base import BaseCommand
from django.db.models import Q
from api.models import CustomUser
from api.models.notifications.in_app_notification import InAppNotification

class Command(BaseCommand):
    help = 'Creates test in-app notifications for users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of notifications to create per user'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email of specific user to create notifications for'
        )

    def handle(self, *args, **options):
        count = options['count']
        email = options.get('email')
        
        # Get users
        if email:
            users = CustomUser.objects.filter(email=email)
            if not users.exists():
                self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
                return
        else:
            # Get all users who are not staff/superusers
            users = CustomUser.objects.filter(
                Q(is_staff=False) & Q(is_superuser=False)
            )
        
        if not users:
            self.stdout.write(self.style.ERROR('No users found to create notifications for'))
            return
            
        notification_types = [
            'medical_record', 
            'test_result', 
            'appointment', 
            'prescription', 
            'payment'
        ]
        
        notification_templates = {
            'medical_record': {
                'title': 'Medical Record Updated',
                'messages': [
                    'Your medical record has been updated with new information.',
                    'New lab results have been added to your medical record.',
                    'Your doctor has added notes to your medical record.'
                ]
            },
            'test_result': {
                'title': 'Test Results Available',
                'messages': [
                    'Your blood test results are now available.',
                    'Your X-ray results have been uploaded.',
                    'The results from your recent test are ready for review.'
                ]
            },
            'appointment': {
                'title': 'Appointment Reminder',
                'messages': [
                    'You have an upcoming appointment tomorrow.',
                    'Your appointment has been confirmed.',
                    'Your appointment has been rescheduled.'
                ]
            },
            'prescription': {
                'title': 'Prescription Update',
                'messages': [
                    'Your prescription has been renewed.',
                    'A new prescription has been added to your account.',
                    'Your medication is ready for pickup.'
                ]
            },
            'payment': {
                'title': 'Payment Notification',
                'messages': [
                    'Your payment was processed successfully.',
                    'Payment receipt is now available.',
                    'You have an outstanding payment due.'
                ]
            }
        }
            
        notifications_created = 0
        for user in users:
            for _ in range(count):
                notification_type = random.choice(notification_types)
                template = notification_templates[notification_type]
                
                InAppNotification.objects.create(
                    user=user,
                    title=template['title'],
                    message=random.choice(template['messages']),
                    notification_type=notification_type,
                    reference_id=f'TEST-{random.randint(1000, 9999)}'
                )
                notifications_created += 1
                
            # Mark some notifications as read
            user_notifications = InAppNotification.objects.filter(user=user)
            for notification in random.sample(
                list(user_notifications), 
                k=min(int(count/3), user_notifications.count())
            ):
                notification.mark_as_read()
                
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {notifications_created} notifications for {users.count()} users'
            )
        ) 