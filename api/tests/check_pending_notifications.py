#!/usr/bin/env python3
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.utils import timezone
from api.models.medical.appointment_notification import AppointmentNotification

# Get pending notifications
pending_notifications = AppointmentNotification.objects.filter(
    status='pending',
    scheduled_time__lte=timezone.now()
)

print(f"Found {pending_notifications.count()} pending notifications that are due to be sent.")

# Get failed notifications that can be retried
from django.db.models import Q
failed_notifications = AppointmentNotification.objects.filter(
    Q(status='failed') & Q(retry_count__lt=AppointmentNotification._meta.get_field('max_retries').default)
)

print(f"Found {failed_notifications.count()} failed notifications that can be retried.")

# Show sample of pending notifications if any exist
if pending_notifications.exists():
    print("\nSample of pending notifications:")
    for notification in pending_notifications[:5]:
        print(f"- ID: {notification.id}")
        print(f"  Type: {notification.get_notification_type_display()}")
        print(f"  Event: {notification.get_event_type_display()}")
        print(f"  Recipient: {notification.recipient.email}")
        print(f"  Subject: {notification.subject}")
        print(f"  Scheduled: {notification.scheduled_time}")
        print()

# Show the most recent notifications in the system
recent_notifications = AppointmentNotification.objects.all().order_by('-created_at')[:5]
if recent_notifications.exists():
    print("\nMost recent notifications created (any status):")
    for notification in recent_notifications:
        print(f"- ID: {notification.id}")
        print(f"  Type: {notification.get_notification_type_display()}")
        print(f"  Event: {notification.get_event_type_display()}")
        print(f"  Status: {notification.get_status_display()}")
        print(f"  Recipient: {notification.recipient.email}")
        print(f"  Subject: {notification.subject}")
        print(f"  Created: {notification.created_at}")
        print()

print("To process pending notifications, run:")
print("python3 manage.py process_pending_notifications [--dry-run] [--retry-failed]") 