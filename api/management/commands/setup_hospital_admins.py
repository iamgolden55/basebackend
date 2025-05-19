import os
import secrets
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from api.models import CustomUser, Hospital
from api.models.medical.hospital_auth import HospitalAdmin

class Command(BaseCommand):
    help = 'Setup existing hospitals with admin accounts for development environment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of admin accounts even if they exist',
        )
        parser.add_argument(
            '--prefix',
            type=str,
            default='admin',
            help='Email prefix for admin accounts (default: admin)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='Password123!',
            help='Default password for all admin accounts',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options['force']
        prefix = options['prefix']
        default_password = options['password']
        
        # Get all hospitals
        hospitals = Hospital.objects.all()
        self.stdout.write(f"Found {hospitals.count()} hospitals to process")
        
        admin_credentials = []
        
        for hospital in hospitals:
            self.stdout.write(f"\nProcessing hospital: {hospital.name} (ID: {hospital.id})")
            
            # Ensure hospital has a registration number for code verification
            if not hospital.registration_number:
                hospital.registration_number = f"H-{secrets.token_hex(4).upper()}"
                hospital.save()
                self.stdout.write(self.style.SUCCESS(
                    f"  - Generated registration number: {hospital.registration_number}"
                ))
            else:
                self.stdout.write(f"  - Registration number: {hospital.registration_number}")
            
            # Find or create hospital admin
            admins = HospitalAdmin.objects.filter(hospital=hospital)
            
            if admins.exists() and not force:
                self.stdout.write(f"  - Hospital already has {admins.count()} admin(s). Use --force to recreate.")
                for admin in admins:
                    self.stdout.write(f"    - {admin.name} ({admin.email})")
                    admin_credentials.append({
                        'hospital': hospital.name,
                        'hospital_id': hospital.id,
                        'hospital_code': hospital.registration_number,
                        'admin_email': admin.email,
                        'admin_name': admin.name,
                        'password': '(existing password)',
                    })
                continue
            
            # Create a new admin account
            hospital_slug = ''.join(c for c in hospital.name.lower() if c.isalnum())[:10]
            
            # Create a slight random variation for each hospital
            random_id = random.randint(1, 999)
            
            admin_email = f"{prefix}.{hospital_slug}{random_id}@example.com"
            admin_name = f"Admin {hospital.name.split()[0]}"
            
            # Create user account first if needed
            user, created = CustomUser.objects.get_or_create(
                email=admin_email,
                defaults={
                    'first_name': 'Hospital',
                    'last_name': f"Admin ({hospital.name.split()[0]})",
                    'password': make_password(default_password),
                    'role': 'hospital_admin',
                    'is_staff': True,  # Give them staff access
                    'is_email_verified': True,  # They're pre-verified
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"  - Created user account: {admin_email}"))
            else:
                self.stdout.write(f"  - Using existing user account: {admin_email}")
            
            # Create or update hospital admin
            admin, created = HospitalAdmin.objects.update_or_create(
                hospital=hospital,
                email=admin_email,
                defaults={
                    'name': admin_name,
                    'position': 'System Administrator',
                    'user': user
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"  - Created hospital admin: {admin_name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"  - Updated hospital admin: {admin_name}"))
            
            admin_credentials.append({
                'hospital': hospital.name,
                'hospital_id': hospital.id,
                'hospital_code': hospital.registration_number,
                'admin_email': admin_email,
                'admin_name': admin_name,
                'password': default_password,
                'is_new': created
            })
        
        # Print summary of all credentials
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("HOSPITAL ADMIN CREDENTIALS SUMMARY"))
        self.stdout.write("="*80)
        self.stdout.write(f"{'HOSPITAL ID':<12} {'HOSPITAL CODE':<20} {'EMAIL':<40} {'PASSWORD':<20}")
        self.stdout.write("-"*80)
        
        for cred in admin_credentials:
            self.stdout.write(
                f"{cred['hospital_id']:<12} {cred['hospital_code']:<20} {cred['admin_email']:<40} {cred['password']:<20}"
            )
            
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS(f"Setup complete for {len(admin_credentials)} hospital admins"))
        self.stdout.write(self.style.WARNING("KEEP THIS INFORMATION SECURE - DEVELOPMENT USE ONLY"))
        self.stdout.write("="*80)
