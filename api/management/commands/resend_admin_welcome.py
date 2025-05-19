# api/management/commands/resend_admin_welcome.py

import os
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from api.models import Hospital, CustomUser
from api.models.medical.hospital_auth import HospitalAdmin

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Resends the welcome email to a hospital admin using their actual contact email'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Email address of the hospital admin')

    def handle(self, *args, **options):
        contact_email = options['email']
        
        try:
            # Find the user and their hospital admin profile
            try:
                user = CustomUser.objects.get(email=contact_email)
                admin = HospitalAdmin.objects.get(user=user)
                hospital = admin.hospital
                
                # Get the credentials
                admin_username = admin.email  # This is their PHB login username (admin.hospital@phb.com)
                contact_email = admin.contact_email or contact_email  # Their real email for communications
                
                # In development mode, ensure we use the proper format
                if settings.DEBUG and not admin_username.endswith('@example.com'):
                    # Generate a development-mode admin username for display
                    admin_username = f"admin.{hospital.name.lower().replace(' ', '')}@example.com"
                elif not settings.DEBUG and not admin_username.endswith('@phb.com'):
                    # Generate a production-mode admin username for display
                    admin_username = f"admin.{hospital.name.lower().replace(' ', '')}@phb.com"
                
                # We don't know their password, so let them know they can reset it
                # In a real scenario, you wouldn't resend the original password
                admin_password = "[Use existing password or reset it]"
                
                # Prepare email context
                context = {
                    'hospital_name': hospital.name,
                    'hospital_code': hospital.registration_number,
                    'admin_email': admin_username,  # This is their PHB username for login
                    'contact_email': contact_email,  # Their real email address
                    'admin_password': admin_password,
                    'login_url': f"{os.environ.get('NEXTJS_URL', 'http://localhost:5173')}/organization/login",
                    'timestamp': timezone.now().strftime('%b %d %Y %H:%M:%S %Z'),
                    'is_development': settings.DEBUG
                }
                
                # Render email template
                html_message = render_to_string('email/hospital_admin_welcome.html', context)
                plain_message = strip_tags(html_message)
                
                # Send email to the ACTUAL contact email (not admin username)
                send_mail(
                    subject=f'PHB Hospital Admin Portal - Secure Login Information - {hospital.name}',
                    message=plain_message,
                    from_email=os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@publichealthbureau.com'),
                    recipient_list=[contact_email],  # Send to their actual email address
                    html_message=html_message,
                    fail_silently=False,
                )
                
                self.stdout.write(self.style.SUCCESS(f"Resent welcome email to: {contact_email}"))
                self.stdout.write(self.style.SUCCESS(f"Hospital: {hospital.name}"))
                self.stdout.write(self.style.SUCCESS(f"Admin username: {admin_username}"))
                self.stdout.write(self.style.SUCCESS(f"Hospital code: {hospital.registration_number}"))
                
            except CustomUser.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"No user found with email: {contact_email}"))
                return
                
            except HospitalAdmin.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User {contact_email} is not a hospital admin"))
                return
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error resending welcome email: {str(e)}"))
