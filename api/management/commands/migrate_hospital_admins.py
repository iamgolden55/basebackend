import os
import secrets
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from api.models import CustomUser, Hospital
from api.models.medical.hospital_auth import HospitalAdmin

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrate existing hospital admins to the new secure login system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--send-emails',
            action='store_true',
            help='Send notification emails to hospital admins about the new login system',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        send_emails = options['send_emails']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - no changes will be made'))
        
        # Get all hospitals
        hospitals = Hospital.objects.all()
        self.stdout.write(f"Found {hospitals.count()} hospitals to process")
        
        # Track statistics
        stats = {
            'total_hospitals': hospitals.count(),
            'hospitals_with_admins': 0,
            'admins_with_valid_emails': 0,
            'admins_requiring_email_update': 0,
            'emails_sent': 0,
            'errors': 0
        }
        
        # Hospitals needing attention (no admins or invalid emails)
        hospitals_needing_attention = []
        
        # Process each hospital
        for hospital in hospitals:
            self.stdout.write(f"\nProcessing hospital: {hospital.name} (ID: {hospital.id})")
            
            # Ensure hospital has a registration number for code verification
            if not hospital.registration_number:
                if not dry_run:
                    hospital.registration_number = f"H-{secrets.token_hex(4).upper()}"
                    hospital.save()
                self.stdout.write(self.style.WARNING(
                    f"  - Generated new registration number: {hospital.registration_number if not dry_run else '[would generate]'}"
                ))
            else:
                self.stdout.write(f"  - Registration number: {hospital.registration_number}")
            
            # Find hospital admins
            admins = HospitalAdmin.objects.filter(hospital=hospital)
            
            if not admins.exists():
                self.stdout.write(self.style.ERROR(f"  - No admin accounts found for this hospital"))
                hospitals_needing_attention.append({
                    'hospital_id': hospital.id,
                    'name': hospital.name,
                    'issue': 'No admin accounts'
                })
                continue
                
            stats['hospitals_with_admins'] += 1
            self.stdout.write(f"  - Found {admins.count()} admin accounts")
            
            # Process each admin
            for admin in admins:
                self.stdout.write(f"  - Processing admin: {admin.name} ({admin.email})")
                
                # Check if admin has a CustomUser account
                if not admin.user:
                    self.stdout.write(self.style.ERROR(f"    - No user account linked to this admin"))
                    continue
                
                # Verify email domain
                email = admin.email
                domain = email.split('@')[-1]
                
                valid_domains = [
                    'medicare.com', 'hospital.org', 'health.gov', 'care.org', 
                    'medical.net', 'clinic.com', 'healthcare.org'
                ]
                
                domain_valid = any(domain.endswith(valid_d) for valid_d in valid_domains)
                import re
                pattern_valid = re.match(r'.*\.(hospital|medical|health|care|clinic)\.(com|org|net|gov)$', domain)
                
                if not (domain_valid or pattern_valid):
                    # Email domain needs to be updated
                    stats['admins_requiring_email_update'] += 1
                    self.stdout.write(self.style.WARNING(
                        f"    - Email domain '{domain}' doesn't match secure hospital format"
                    ))
                    
                    # Suggest a new email
                    hospital_slug = hospital.name.lower().replace(' ', '')[:10]
                    suggested_email = f"{admin.name.split()[0].lower()}.{admin.name.split()[-1].lower()}@{hospital_slug}.healthcare.org"
                    
                    self.stdout.write(self.style.WARNING(
                        f"    - Suggested email: {suggested_email}"
                    ))
                    
                    hospitals_needing_attention.append({
                        'hospital_id': hospital.id,
                        'name': hospital.name,
                        'admin_id': admin.id,
                        'admin_name': admin.name,
                        'current_email': admin.email,
                        'suggested_email': suggested_email,
                        'issue': 'Invalid email domain'
                    })
                else:
                    stats['admins_with_valid_emails'] += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"    - Email domain is valid for hospital admin"
                    ))
                    
                    # Send notification email if requested
                    if send_emails and not dry_run:
                        try:
                            self._send_notification_email(admin, hospital)
                            stats['emails_sent'] += 1
                            self.stdout.write(self.style.SUCCESS(
                                f"    - Sent notification email about new login system"
                            ))
                        except Exception as e:
                            stats['errors'] += 1
                            self.stdout.write(self.style.ERROR(
                                f"    - Failed to send email: {str(e)}"
                            ))
                    elif send_emails and dry_run:
                        self.stdout.write(self.style.WARNING(
                            f"    - Would send notification email (dry run)"
                        ))
        
        # Print summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("Migration Summary:"))
        self.stdout.write(f"Total hospitals: {stats['total_hospitals']}")
        self.stdout.write(f"Hospitals with admins: {stats['hospitals_with_admins']}")
        self.stdout.write(f"Admins with valid emails: {stats['admins_with_valid_emails']}")
        self.stdout.write(f"Admins requiring email updates: {stats['admins_requiring_email_update']}")
        
        if send_emails:
            self.stdout.write(f"Notification emails sent: {stats['emails_sent']}")
        
        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f"Errors encountered: {stats['errors']}"))
            
        # Print hospitals needing attention
        if hospitals_needing_attention:
            self.stdout.write("\n" + "="*50)
            self.stdout.write(self.style.WARNING("Hospitals Needing Attention:"))
            for hospital in hospitals_needing_attention:
                self.stdout.write(f"- {hospital['name']} (ID: {hospital['hospital_id']}): {hospital['issue']}")
                if 'admin_name' in hospital:
                    self.stdout.write(f"  Admin: {hospital['admin_name']} ({hospital['current_email']})")
                    if 'suggested_email' in hospital:
                        self.stdout.write(f"  Suggested email: {hospital['suggested_email']}")
                        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nThis was a dry run. No changes were made."))
        else:
            self.stdout.write(self.style.SUCCESS("\nMigration completed."))
    
    def _send_notification_email(self, admin, hospital):
        """Send notification email about the new login system"""
        context = {
            'admin_name': admin.name,
            'hospital_name': hospital.name,
            'hospital_code': hospital.registration_number,
            'effective_date': (timezone.now() + timezone.timedelta(days=7)).strftime('%B %d, %Y')
        }
        
        html_message = render_to_string('email/hospital_admin_migration.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=f'Important: New Secure Login System for {hospital.name} Administrators',
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            recipient_list=[admin.email],
            html_message=html_message,
            fail_silently=False,
        )
