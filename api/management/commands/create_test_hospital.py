# api/management/commands/create_test_hospital.py

import os
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.utils import timezone

from api.models import Hospital, CustomUser
from api.models.medical.hospital_auth import HospitalAdmin

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Creates a test hospital with specified admin email for demonstration purposes'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True, help='Hospital name')
        parser.add_argument('--admin_email', type=str, required=True, help='Email for the hospital admin')
        parser.add_argument('--type', type=str, default='specialist', choices=['public', 'private', 'specialist', 'teaching', 'clinic', 'research'], help='Hospital type')
        parser.add_argument('--city', type=str, default='Lagos', help='Hospital city')
        parser.add_argument('--password', type=str, default='Password123!', help='Admin password')

    def handle(self, *args, **options):
        hospital_name = options['name']
        admin_email = options['admin_email']
        hospital_type = options['type']
        city = options['city']
        password = options['password']

        try:
            with transaction.atomic():
                # Create hospital
                hospital = Hospital.objects.create(
                    name=hospital_name,
                    hospital_type=hospital_type,
                    city=city,
                    address=f"{hospital_name}, {city}",
                    is_verified=True,
                    verification_date=timezone.now().date(),
                    email=admin_email  # Store the contact email in the hospital record
                )
                
                # Generate registration number if not created by model save
                if not hospital.registration_number:
                    hospital.registration_number = f"HOS-{hospital.id:04d}"
                    hospital.save()
                    
                # Set the contact email as metadata for the admin creation signal
                if not hasattr(hospital, '_meta'):
                    hospital._meta = lambda: None
                hospital._meta.contact_email = admin_email
                
                # Check if user exists already
                try:
                    admin_user = CustomUser.objects.get(email=admin_email)
                    self.stdout.write(self.style.SUCCESS(f"Found existing user: {admin_email}"))
                    
                    # Update existing user to be hospital admin
                    admin_user.role = 'hospital_admin'
                    admin_user.is_staff = True
                    admin_user.save()
                    
                    # Set/reset password if requested
                    if options.get('reset_password', True):
                        admin_user.set_password(password)
                        admin_user.save()
                        self.stdout.write(self.style.SUCCESS(f"Password updated for existing user"))
                    
                except CustomUser.DoesNotExist:
                    # Create new hospital admin user
                    admin_user = CustomUser.objects.create_user(
                        username=admin_email,
                        email=admin_email,
                        password=password,
                        first_name="Hospital",
                        last_name=f"Admin ({hospital_name[0:4]})",
                        role="hospital_admin",
                        is_staff=True,
                        is_email_verified=True
                    )
                
                # Check if hospital admin profile already exists
                admin, created = HospitalAdmin.objects.update_or_create(
                    user=admin_user,
                    defaults={
                        'hospital': hospital,
                        'name': f"Hospital Admin for {hospital_name}",
                        'position': "System Administrator",
                        'email': admin_email,
                        'password_change_required': True  # Require password change on first login
                    }
                )
                
                # Log whether we created or updated
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created new hospital admin profile"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"Updated existing hospital admin profile"))
                
                self.stdout.write(self.style.SUCCESS(f"Created test hospital: {hospital_name}"))
                self.stdout.write(self.style.SUCCESS(f"Hospital code: {hospital.registration_number}"))
                self.stdout.write(self.style.SUCCESS(f"Admin email: {admin_email}"))
                self.stdout.write(self.style.SUCCESS(f"Admin password: {password}"))
                self.stdout.write(self.style.SUCCESS(f"\nLogin URL: http://localhost:3000/hospital-admin/login"))
                self.stdout.write(self.style.SUCCESS(f"\nNote: Password change will be required on first login."))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating test hospital: {str(e)}"))
