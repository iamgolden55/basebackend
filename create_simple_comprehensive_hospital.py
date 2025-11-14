#!/usr/bin/env python
import os
import sys
import django
from datetime import date, datetime
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical import Hospital

def create_simple_comprehensive_hospital():
    print("Creating Royal Medicare Hospital with all comprehensive fields...")
    
    # Check if Royal Medicare Hospital already exists and delete it
    existing_hospitals = Hospital.objects.filter(name="Royal Medicare Hospital")
    if existing_hospitals.exists():
        print(f"Found {existing_hospitals.count()} existing Royal Medicare Hospital(s). Deleting them...")
        existing_hospitals.delete()
        print("✅ Deleted existing Royal Medicare Hospital(s)")
    
    # Create the comprehensive hospital with all fields from the documentation
    hospital = Hospital.objects.create(
        # Basic Information
        name="Royal Medicare Hospital",
        address="456 Wellness Avenue, Ikoyi, Lagos, Nigeria",
        phone="+234-802-345-6789",
        email="admin@royalmedcare.hospital",
        website="https://www.royalmedcare.hospital",
        
        # Location Information
        latitude=Decimal('6.4541'),
        longitude=Decimal('3.4316'),
        city="Lagos",
        state="Lagos State",
        country="Nigeria",
        postal_code="101001",
        
        # Registration and Verification
        registration_number="HOSP-NG-2024-004",
        is_verified=False,
        verification_date=None,
        
        # Hospital Type and Classification
        hospital_type="private",
        
        # Operational Information
        bed_capacity=200,
        emergency_unit=True,
        icu_unit=True,
        
        # Contact Information
        emergency_contact="+234-802-345-6789",
        
        # Accreditation and Certification
        accreditation_status=False,
        accreditation_expiry=None
    )
    
    print(f"\n🎉 Successfully created Royal Medicare Hospital with comprehensive setup!")
    print(f"Hospital ID: {hospital.id}")
    print(f"Hospital Name: {hospital.name}")
    print(f"Registration Number: {hospital.registration_number}")
    print(f"Address: {hospital.address}")
    print(f"Type: {hospital.get_hospital_type_display()}")
    print(f"Bed Capacity: {hospital.bed_capacity}")
    print(f"Emergency Unit: {hospital.emergency_unit}")
    print(f"ICU Unit: {hospital.icu_unit}")
    print(f"Phone: {hospital.phone}")
    print(f"Email: {hospital.email}")
    print(f"Website: {hospital.website}")
    print(f"Coordinates: {hospital.latitude}, {hospital.longitude}")
    print(f"City: {hospital.city}")
    print(f"State: {hospital.state}")
    print(f"Country: {hospital.country}")
    print(f"Postal Code: {hospital.postal_code}")
    print(f"Verified: {hospital.is_verified}")
    
    print(f"\n📋 Hospital created with all comprehensive fields as shown in:")
    print(f"   /Users/new/Newphb/basebackend/docs/HOSPITAL_CREATION_COMPREHENSIVE_JSON.md")
    print(f"\n✨ This hospital includes all the basic information fields and is ready for:")
    print(f"   • Government license applications")
    print(f"   • Insurance provider relationships")
    print(f"   • Quality certifications")
    print(f"   • Compliance framework setup")
    print(f"   • Billing system integration")
    
    return hospital

if __name__ == "__main__":
    try:
        hospital = create_simple_comprehensive_hospital()
        print("\n✅ Hospital creation completed successfully!")
    except Exception as e:
        print(f"\n❌ Error creating hospital: {str(e)}")
        import traceback
        traceback.print_exc()