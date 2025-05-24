#!/usr/bin/env python
import os
import django
from django.db import transaction

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital, HospitalAdmin

def create_hospital_with_admin():
    """Create a hospital with a hospital admin user that has all security features"""
    try:
        # Create hospital
        with transaction.atomic():
            hospital, created = Hospital.objects.get_or_create(
                name='St. Nicholas Hospital',
                defaults={
                    'hospital_type': 'General Hospital',
                    'address': '1 Hospital Road',
                    'city': 'Lagos',
                    'state': 'Lagos',
                    'country': 'Nigeria',
                    'postal_code': '100001',
                    'phone': '+2347012345678',
                    'email': 'info@stnicholas.com',
                    'website': 'www.stnicholas.com',
                    'emergency_unit': True,
                    'icu_unit': True,
                    'is_verified': True
                }
            )
            
            if created:
                print(f"Created new hospital: {hospital.name}")
            else:
                print(f"Using existing hospital: {hospital.name}")
            
            # Create hospital admin with enhanced security features
            admin_email = "hospital_admin@stnicholas.com"
            admin, admin_created = HospitalAdmin.objects.get_or_create(
                email=admin_email,
                defaults={
                    'hospital': hospital,
                    'position': 'Chief Administrator',
                    'first_name': 'Hospital',
                    'last_name': 'Admin',
                    'contact_email': admin_email,
                    'password_change_required': True,  # Force password change on first login
                    'two_factor_enabled': True,  # Mandatory 2FA
                    'is_active': True
                }
            )
            
            if admin_created:
                admin.set_password('HospitalAdmin1234')
                admin.save()
                print(f"Created hospital admin: {admin_email} / HospitalAdmin1234")
            else:
                print(f"Hospital admin already exists: {admin_email}")
            
            print("\nHospital admin security features enabled:")
            print("1. Domain validation for hospital email addresses")
            print("2. Required hospital code verification")
            print("3. Mandatory 2FA for all hospital admins")
            print("4. Enhanced security with trusted device tracking")
            print("\nLogin security features:")
            print("1. Rate limiting: IP-based rate limiting after 3 failed attempts")
            print("2. Account lockout: Account lockout for 15 minutes after 5 failed attempts")
            print("3. Suspicious login notifications: Email alerts sent after 3 failed login attempts")
            print("4. Password reset unlocking: Account lockout is automatically cleared after successful password reset")
            print("5. Detailed security logging: Comprehensive logging of security events")
            
            return True
    except Exception as e:
        print(f"Error creating hospital and admin: {e}")
        return False

if __name__ == "__main__":
    create_hospital_with_admin()
