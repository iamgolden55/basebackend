"""
Test script for hospital registration approval email

This script tests the email sending functionality when a hospital approves
a patient's registration request.

Usage:
    python manage.py shell < api/tests/test_hospital_registration_email.py

Or in Django shell:
    exec(open('api/tests/test_hospital_registration_email.py').read())
"""

import os
import django
from datetime import datetime
from django.utils import timezone

# Ensure Django settings are configured
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.utils.email import send_hospital_registration_approved_email

def test_hospital_registration_approval_email():
    """
    Test sending hospital registration approval email with sample data
    """
    print("\n" + "="*80)
    print("TESTING HOSPITAL REGISTRATION APPROVAL EMAIL")
    print("="*80 + "\n")

    # Sample test data
    test_data = {
        'patient_email': 'test.patient@example.com',  # Change to real email for testing
        'patient_name': 'John Doe',
        'hospital_name': 'St. Nicholas Hospital',
        'hospital_address': '123 Medical Drive, Victoria Island, Lagos, Nigeria',
        'approval_date': timezone.now(),
        'hpn': 'PHB-2025-001234',
        'hospital_phone': '+234 1 234 5678',
        'hospital_email': 'info@stnicholas.ng',
        'hospital_profile_url': 'http://localhost:3001/hospitals/1'
    }

    print("Test Data:")
    print("-" * 80)
    for key, value in test_data.items():
        print(f"  {key}: {value}")
    print("-" * 80 + "\n")

    # Send test email
    print("Sending test email...")
    try:
        result = send_hospital_registration_approved_email(**test_data)

        if result:
            print("\n✅ SUCCESS: Email sent successfully!")
            print(f"   Email sent to: {test_data['patient_email']}")
            print(f"   Hospital: {test_data['hospital_name']}")
            print(f"   Subject: Hospital Registration Approved ✅ - {test_data['hospital_name']}")
        else:
            print("\n❌ FAILED: Email sending returned False")
            print("   Check the error logs for details")

    except Exception as e:
        print(f"\n❌ ERROR: Exception occurred while sending email")
        print(f"   Error: {str(e)}")
        import traceback
        print("\nFull traceback:")
        print("-" * 80)
        traceback.print_exc()
        print("-" * 80)

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

def test_with_real_registration():
    """
    Test with an actual hospital registration from the database
    Requires at least one approved registration in the database
    """
    from api.models import HospitalRegistration

    print("\n" + "="*80)
    print("TESTING WITH REAL REGISTRATION DATA")
    print("="*80 + "\n")

    # Get the most recent approved registration
    registration = HospitalRegistration.objects.filter(
        status='approved'
    ).order_by('-approved_date').first()

    if not registration:
        print("❌ No approved registrations found in database")
        print("   Please approve a registration first or use test_hospital_registration_approval_email()")
        return

    print(f"Found registration:")
    print(f"  ID: {registration.id}")
    print(f"  Patient: {registration.user.get_full_name()}")
    print(f"  Email: {registration.user.email}")
    print(f"  Hospital: {registration.hospital.name}")
    print(f"  Status: {registration.status}")
    print(f"  Approved: {registration.approved_date}")
    print()

    # Get patient details
    patient = registration.user
    hospital = registration.hospital

    # Get patient's full name
    patient_full_name = patient.get_full_name() if hasattr(patient, 'get_full_name') else f"{patient.first_name} {patient.last_name}"

    # Format hospital address
    hospital_address_parts = []
    if hospital.address_line_1:
        hospital_address_parts.append(hospital.address_line_1)
    if hospital.address_line_2:
        hospital_address_parts.append(hospital.address_line_2)
    if hospital.city:
        hospital_address_parts.append(hospital.city)
    if hospital.state:
        hospital_address_parts.append(hospital.state)
    if hospital.country:
        hospital_address_parts.append(hospital.country)

    hospital_address = ", ".join(hospital_address_parts) if hospital_address_parts else "Address not available"

    # Send email
    print("Sending email...")
    try:
        result = send_hospital_registration_approved_email(
            patient_email=patient.email,
            patient_name=patient_full_name,
            hospital_name=hospital.name,
            hospital_address=hospital_address,
            approval_date=registration.approved_date or timezone.now(),
            hpn=patient.hpn if hasattr(patient, 'hpn') else None,
            hospital_phone=hospital.phone if hasattr(hospital, 'phone') else None,
            hospital_email=hospital.email if hasattr(hospital, 'email') else None,
            hospital_profile_url=None
        )

        if result:
            print("\n✅ SUCCESS: Email sent successfully!")
            print(f"   Email sent to: {patient.email}")
        else:
            print("\n❌ FAILED: Email sending returned False")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

# Run the test
if __name__ == "__main__":
    print("\n")
    print("HOSPITAL REGISTRATION EMAIL TEST SUITE")
    print("="*80)
    print("\nAvailable test functions:")
    print("  1. test_hospital_registration_approval_email() - Test with sample data")
    print("  2. test_with_real_registration() - Test with real database registration")
    print("\nRunning test with sample data...\n")

    test_hospital_registration_approval_email()

    print("\nTo test with real data, run:")
    print("  >>> test_with_real_registration()")
