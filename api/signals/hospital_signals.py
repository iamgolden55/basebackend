# api/signals/hospital_signals.py

import os
import uuid
import secrets
import logging
import string
import random
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db import transaction

from api.models import Hospital, CustomUser
from api.models.medical.hospital_auth import HospitalAdmin

logger = logging.getLogger(__name__)


def generate_secure_password():
    """
    Generate a secure password following best practices for hospital admins.
    The password has a minimum length of 12 characters and includes uppercase, lowercase,
    digits, and special characters.
    """
    length = 12
    
    # Ensure we have at least one of each character type
    uppercase = random.choice(string.ascii_uppercase)
    lowercase = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    special = random.choice('!@#$%^&*()-_=+[]{}|;:,.<>?')
    
    # Fill the rest with a mix of all characters
    remaining_length = length - 4
    all_chars = string.ascii_letters + string.digits + '!@#$%^&*()-_=+[]{}|;:,.<>?'
    remaining_chars = ''.join(random.choice(all_chars) for _ in range(remaining_length))
    
    # Combine all parts and shuffle
    password_chars = list(uppercase + lowercase + digit + special + remaining_chars)
    random.shuffle(password_chars)
    return ''.join(password_chars)


@receiver(post_save, sender=Hospital)
def create_hospital_admin_account(sender, instance, created, **kwargs):
    """
    Signal handler to automatically create a hospital admin account when a new hospital is created.
    
    This handler ensures every new hospital has an administrator account with:
    1. A secure generated password
    2. An email with admin credentials
    """
    if created:  # Only proceed for newly created hospitals
        try:
            # Generate admin credentials
            hospital = instance
            real_contact_email = None  # This will hold the actual email for communications
            
            # Check if a contact email was provided during hospital registration
            # Could be stored in hospital.email or passed through _meta
            if hasattr(hospital, 'email') and hospital.email:
                real_contact_email = hospital.email
            elif hasattr(instance, '_meta') and hasattr(instance._meta, 'contact_email'):
                real_contact_email = instance._meta.contact_email
                
            # Generate standardized PHB admin username - this is what they'll use to login
            # This is NOT a real email inbox, just a username format
            # Always generate secure password regardless of environment
            admin_password = generate_secure_password()

            if settings.DEBUG:
                # Development format - using example.com domain
                admin_username = f"admin.{hospital.name.lower().replace(' ', '')}@example.com"
            else:
                # Production format - using phb.com domain
                admin_username = f"admin.{hospital.name.lower().replace(' ', '')}@phb.com"
            
            # Create the CustomUser account with hospital admin role
            with transaction.atomic():
                user = CustomUser.objects.create_user(
                    username=admin_username,  # Use the standardized admin username format
                    email=admin_username,  # Use admin username for login authentication
                    password=admin_password,
                    first_name="Hospital",
                    last_name=f"Admin ({hospital.name[0:4]})",
                    role="hospital_admin",
                    is_staff=True,  # Hospital admins have staff privileges
                    is_email_verified=True,  # Auto-verify for immediate access
                )

                # Link user to hospital for permission checks
                user.hospital = hospital
                user.save()

                # Create the HospitalAdmin profile
                admin = HospitalAdmin.objects.create(
                    user=user,
                    hospital=hospital,
                    name=f"Hospital Admin for {hospital.name}",
                    position="System Administrator",
                    email=admin_username,  # Store the login username for authentication
                    contact_email=real_contact_email  # Store the real contact email for notifications
                )
                
                logger.info(f"Created hospital admin account for: {hospital.name}")
                
                # Send welcome email with credentials to their real email if we have it
                # Otherwise use the admin username (though this would only work if it's a real email)
                contact_email = real_contact_email or admin_username
                send_hospital_admin_credentials(hospital, contact_email, admin_password, admin_username)
                
        except Exception as e:
            logger.error(f"Failed to create hospital admin account: {str(e)}")


def send_hospital_admin_credentials(hospital, contact_email, password, admin_username):
    """
    Send the hospital admin their login credentials via email.
    
    Args:
        hospital: The Hospital object
        contact_email: The real email address where we send communications
        password: The generated password
        admin_username: The system-generated username (admin.hospitalname@phb.com format)
    """
    try:
        # Prepare email context
        context = {
            'hospital_name': hospital.name,
            'hospital_code': hospital.registration_number,
            'admin_email': admin_username,  # This is their login username (like admin.hospitalname@phb.com)
            'contact_email': contact_email,  # This is their real email address where they receive communications
            'admin_password': password,
            'login_url': f"{os.environ.get('NEXTJS_URL', 'http://localhost:5173')}/organization/login",
            'timestamp': timezone.now().strftime('%b %d %Y %H:%M:%S %Z'),
            'is_development': settings.DEBUG
        }
        
        # Render email template
        html_message = render_to_string('email/hospital_admin_welcome.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email to the contact email, not the admin username
        send_mail(
            subject=f'Hospital Admin Account Created - {hospital.name}',
            message=plain_message,
            from_email=os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@publichealthbureau.com'),
            # Important: This should be the real contact email where the admin can receive mail
            recipient_list=[contact_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Sent welcome email with credentials to hospital admin: {contact_email}")
        
    except Exception as e:
        logger.error(f"Failed to send hospital admin credentials email: {str(e)}")
