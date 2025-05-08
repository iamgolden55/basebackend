from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.models.notifications.in_app_notification import InAppNotification

class Command(BaseCommand):
    help = 'Clean up old notifications from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Delete notifications older than this many days'
        )
        parser.add_argument(
            '--read-only',
            action='store_true',
            help='Delete only read notifications'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        read_only = options['read_only']
        dry_run = options['dry_run']
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Build query to find old notifications
        query = InAppNotification.objects.filter(created_at__lt=cutoff_date)
        if read_only:
            query = query.filter(is_read=True)
        
        # Count notifications to be deleted
        count = query.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'Would delete {count} notifications older than {days} days'
                    f'{" (read only)" if read_only else ""}'
                )
            )
        else:
            # Delete notifications
            deleted, _ = query.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted} notifications older than {days} days'
                    f'{" (read only)" if read_only else ""}'
                )
            ) 