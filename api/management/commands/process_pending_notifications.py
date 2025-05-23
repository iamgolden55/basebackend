from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
from api.models.medical.appointment_notification import AppointmentNotification

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process all pending appointment notifications that are due to be sent'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max',
            type=int,
            default=100,
            help='Maximum number of notifications to process'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending'
        )
        parser.add_argument(
            '--retry-failed',
            action='store_true',
            help='Also retry failed notifications (within retry limits)'
        )

    def handle(self, *args, **options):
        max_notifications = options['max']
        dry_run = options['dry_run']
        retry_failed = options['retry_failed']
        
        self.stdout.write(
            f"Processing up to {max_notifications} pending appointment notifications..."
        )
        
        # Get pending notifications that are due
        pending_query = AppointmentNotification.objects.filter(
            status='pending',
            scheduled_time__lte=timezone.now()
        )
        
        # Also include failed notifications if requested
        if retry_failed:
            from django.db.models import Q
            pending_query = pending_query | AppointmentNotification.objects.filter(
                Q(status='failed') & Q(retry_count__lt=AppointmentNotification._meta.get_field('max_retries').default)
            )
            
        # Order by scheduled time and limit the number of notifications to process
        notifications = pending_query.order_by('scheduled_time')[:max_notifications]
        
        count = notifications.count()
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS("No pending notifications to process.")
            )
            return
            
        self.stdout.write(
            f"Found {count} notifications to process."
        )
            
        success_count = 0
        error_count = 0
        
        for notification in notifications:
            recipient = notification.recipient.email
            notification_type = notification.get_notification_type_display()
            
            self.stdout.write(
                f"Processing {notification_type} notification for {recipient}: "
                f"{notification.subject} ({notification.id})"
            )
            
            if dry_run:
                self.stdout.write(self.style.WARNING("Dry run - not sending"))
                continue
                
            try:
                success = notification.send()
                if success:
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Sent successfully")
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f"✗ Failed to send: {notification.error_message}")
                    )
            except Exception as e:
                error_count += 1
                logger.exception(f"Error processing notification {notification.id}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f"✗ Exception: {str(e)}")
                )
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dry run completed for {count} notifications."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Processed {count} notifications: {success_count} succeeded, {error_count} failed."
                )
            ) 