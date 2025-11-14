"""
Management command to notify patients about unaccepted appointments that have passed their scheduled time.

This command should be run periodically (e.g., every 15 minutes via cron) to check for appointments
that are past their scheduled time and still pending (no doctor has accepted them).

Usage:
    python manage.py notify_unaccepted_appointments
    python manage.py notify_unaccepted_appointments --dry-run  # Preview without sending
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models.medical.appointment import Appointment
from api.models.medical.appointment_notification import AppointmentNotification
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Notify patients about appointments that passed scheduled time without doctor acceptance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview notifications without actually sending them',
        )
        parser.add_argument(
            '--grace-period',
            type=int,
            default=5,
            help='Grace period in minutes after scheduled time before sending notification (default: 5)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        grace_period_minutes = options['grace_period']

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*80}\n'
            f'🔍 Checking for Unaccepted Appointments Past Scheduled Time\n'
            f'{"="*80}\n'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  DRY RUN MODE - No notifications will be sent\n'))

        # Calculate the cutoff time (grace period ago)
        grace_period = timezone.timedelta(minutes=grace_period_minutes)
        cutoff_time = timezone.now() - grace_period

        self.stdout.write(f'⏰ Current time: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write(f'⏱️  Grace period: {grace_period_minutes} minutes')
        self.stdout.write(f'📅 Cutoff time: {cutoff_time.strftime("%Y-%m-%d %H:%M:%S")}\n')

        # Find all pending appointments that are past their scheduled time
        # and haven't been notified yet about being unaccepted
        overdue_appointments = Appointment.objects.filter(
            status='pending',
            doctor__isnull=True,  # No doctor assigned
            appointment_date__lt=cutoff_time  # Past the grace period
        ).select_related('patient', 'hospital', 'department')

        total_count = overdue_appointments.count()
        self.stdout.write(f'📊 Found {total_count} overdue pending appointments\n')

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ No unaccepted appointments to notify about'))
            return

        # Filter out appointments that have already been notified
        appointments_to_notify = []
        for appointment in overdue_appointments:
            # Check if we've already sent an unaccepted notification for this appointment
            existing_notification = AppointmentNotification.objects.filter(
                appointment=appointment,
                event_type='appointment_unaccepted'
            ).exists()

            if not existing_notification:
                appointments_to_notify.append(appointment)

        notify_count = len(appointments_to_notify)
        self.stdout.write(
            f'📧 {notify_count} appointments need notification '
            f'({total_count - notify_count} already notified)\n'
        )

        if notify_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ All overdue appointments have been notified'))
            return

        # Display appointments to be notified
        self.stdout.write(self.style.WARNING('\n📋 Appointments to notify:\n'))
        for appointment in appointments_to_notify:
            minutes_overdue = int((timezone.now() - appointment.appointment_date).total_seconds() / 60)
            self.stdout.write(
                f'  • {appointment.appointment_id}: '
                f'{appointment.patient.get_full_name()} | '
                f'Scheduled: {appointment.appointment_date.strftime("%Y-%m-%d %H:%M")} | '
                f'{minutes_overdue} min overdue'
            )

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  DRY RUN - Skipping notification sending\n'))
            self.stdout.write(self.style.SUCCESS('✅ Dry run completed successfully'))
            return

        # Send notifications
        self.stdout.write(self.style.WARNING('\n📤 Sending notifications...\n'))

        success_count = 0
        error_count = 0

        for appointment in appointments_to_notify:
            try:
                # Create email notification
                notification = AppointmentNotification.objects.create(
                    appointment=appointment,
                    notification_type='email',
                    event_type='appointment_unaccepted',
                    recipient=appointment.patient,
                    subject=f'Appointment Update - {appointment.appointment_id}',
                    message=(
                        f'Dear {appointment.patient.get_full_name()},\n\n'
                        f'Your appointment scheduled for {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")} '
                        f'at {appointment.hospital.name} ({appointment.department.name}) has not been accepted by a doctor yet.\n\n'
                        f'Your appointment has been flagged as pending and is now visible to all available doctors in the department. '
                        f'A doctor will review and accept your appointment shortly, and may propose a new convenient time.\n\n'
                        f'You will be notified once a doctor accepts your appointment.\n\n'
                        f'Appointment ID: {appointment.appointment_id}\n'
                        f'Original Time: {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")}\n\n'
                        f'We apologize for the delay and appreciate your patience.\n\n'
                        f'Best regards,\n'
                        f'{appointment.hospital.name}'
                    ),
                    template_name='appointment_unaccepted'
                )

                # Create SMS notification if phone number available
                if appointment.patient.phone:
                    AppointmentNotification.objects.create(
                        appointment=appointment,
                        notification_type='sms',
                        event_type='appointment_unaccepted',
                        recipient=appointment.patient,
                        subject=f'Appt Update: {appointment.appointment_id}',
                        message=(
                            f'Your appointment at {appointment.hospital.name} on '
                            f'{appointment.appointment_date.strftime("%b %d, %I:%M %p")} is pending. '
                            f'A doctor will review and may propose a new time. ID: {appointment.appointment_id}'
                        )
                    )

                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Sent notification for {appointment.appointment_id}')
                )

            except Exception as e:
                error_count += 1
                logger.error(f'Failed to notify appointment {appointment.appointment_id}: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Failed for {appointment.appointment_id}: {str(e)}')
                )

        # Summary
        self.stdout.write(
            f'\n{"="*80}\n'
            f'📊 Summary\n'
            f'{"="*80}\n'
        )
        self.stdout.write(f'✅ Successfully notified: {success_count}')
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Errors: {error_count}'))
        self.stdout.write(self.style.SUCCESS(f'\n✨ Notification process completed\n'))
