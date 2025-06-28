# api/management/commands/cleanup_expired_otps.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.services.womens_health_verification import WomensHealthVerificationService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up expired women\'s health verification OTPs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it',
        )
        parser.add_argument(
            '--expiry-minutes',
            type=int,
            default=WomensHealthVerificationService.OTP_EXPIRY_MINUTES,
            help=f'OTP expiry time in minutes (default: {WomensHealthVerificationService.OTP_EXPIRY_MINUTES})',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        expiry_minutes = options['expiry_minutes']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting cleanup of OTPs older than {expiry_minutes} minutes...'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        try:
            if dry_run:
                # Calculate what would be cleaned up
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                expiry_threshold = timezone.now() - timedelta(minutes=expiry_minutes)
                
                expired_otps = User.objects.filter(
                    womens_health_otp__isnull=False,
                    womens_health_otp_created_at__lt=expiry_threshold
                )
                
                count = expired_otps.count()
                
                self.stdout.write(f'Would clean up {count} expired OTPs')
                
                for user in expired_otps[:10]:  # Show first 10 as examples
                    time_ago = timezone.now() - user.womens_health_otp_created_at
                    self.stdout.write(
                        f'  - User {user.id} ({user.email}): OTP created {time_ago} ago'
                    )
                
                if count > 10:
                    self.stdout.write(f'  ... and {count - 10} more')
                    
            else:
                # Actually clean up
                count = WomensHealthVerificationService.cleanup_expired_otps()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully cleaned up {count} expired OTPs')
                )
                
                if count > 0:
                    logger.info(f'Cleaned up {count} expired OTPs via management command')
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during cleanup: {str(e)}')
            )
            logger.error(f'Error during OTP cleanup: {str(e)}')
            return
        
        self.stdout.write(
            self.style.SUCCESS('Cleanup completed successfully')
        )