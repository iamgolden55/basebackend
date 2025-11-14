#!/usr/bin/env python
"""
Script to register a test doctor for General Hospital Asaba
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Hospital
from api.models.registry import ProfessionalApplication
from django.utils import timezone
from datetime import datetime

User = get_user_model()

def register_test_doctor():
    """Register a test doctor for General Hospital Asaba"""
    
    # Get the hospital
    try:
        hospital = Hospital.objects.get(id=27)
        print(f"✅ Found hospital: {hospital.name}")
    except Hospital.DoesNotExist:
        print("❌ Hospital not found!")
        return
    
    # Check if doctor email already exists
    email = "dr.emmanuel.okonkwo@phb-test.com"
    if User.objects.filter(email=email).exists():
        print(f"⚠️  User with email {email} already exists")
        user = User.objects.get(email=email)
        print(f"   User: {user.first_name} {user.last_name}")
        print(f"   Role: {user.role}")
        print(f"   Hospital: {user.hospital}")
        
        # Update user to be a doctor at this hospital
        user.role = 'doctor'
        user.hospital = hospital
        user.is_email_verified = True
        user.save()
        print(f"✅ Updated existing user to doctor at {hospital.name}")
        
    else:
        # Create new user
        user = User.objects.create_user(
            username=email,
            email=email,
            password='TestDoctor123!',
            first_name='Emmanuel',
            last_name='Okonkwo',
            phone='+2348012345678',
            date_of_birth='1985-05-15',
            role='doctor',
            hospital=hospital,
            city='Asaba',
            state='Delta',
            country='Nigeria',
            is_email_verified=True,
            is_active=True
        )
        print(f"✅ Created new user: {user.first_name} {user.last_name}")
    
    # Check if professional application already exists
    reg_number = "MDCN/R/2024/12345"
    app = ProfessionalApplication.objects.filter(
        home_registration_number=reg_number
    ).first()
    
    if app:
        print(f"⚠️  Professional application already exists: {app.application_reference}")
        print(f"   Status: {app.status}")
        
        # Update application to approved if not already
        if app.status != 'approved':
            app.status = 'approved'
            app.approved_date = timezone.now()
            app.save()
            print(f"✅ Approved application")
    else:
        # Create professional application with correct field names
        app = ProfessionalApplication.objects.create(
            user=user,
            professional_type='doctor',
            title='Dr',
            first_name='Emmanuel',
            middle_name='Chukwuma',
            last_name='Okonkwo',
            email=email,
            phone='+2348012345678',
            date_of_birth='1985-05-15',
            gender='male',
            nationality='Nigerian',
            
            # Address (use correct field names)
            address_line_1='45 Medical Quarters, GRA',
            address_line_2='',
            city='Asaba',
            state='Delta',
            postcode='',
            country='Nigeria',
            
            # Regulatory info
            home_registration_body='MDCN',
            home_registration_number=reg_number,
            home_registration_date='2024-01-15',
            
            # Education (use correct field names)
            primary_qualification='MBBS',
            qualification_institution='University of Lagos',
            qualification_year=2010,
            qualification_country='Nigeria',
            additional_qualifications=[
                {'degree': 'Fellowship in Internal Medicine', 'institution': 'FMCPaed', 'year': 2015},
                {'degree': 'Certificate in Emergency Medicine', 'institution': 'West African College', 'year': 2018}
            ],
            
            # Professional details
            years_of_experience=14,
            specialization='internal_medicine',
            subspecialization='',
            employment_history=[
                {
                    'employer': 'New General Central Hospital GRA Asaba',
                    'position': 'Consultant Physician',
                    'from_date': '2015-01-01',
                    'to_date': 'present',
                    'responsibilities': 'Internal Medicine consultations, patient care'
                }
            ],
            
            # Application status
            status='approved',
            decision_date=timezone.now(),
            submitted_date=timezone.now()
        )
        print(f"✅ Created professional application: {app.application_reference}")
    
    # Summary
    print("\n" + "="*60)
    print("REGISTRATION COMPLETE")
    print("="*60)
    print(f"Doctor: Dr. {user.first_name} {user.last_name}")
    print(f"Email: {user.email}")
    print(f"Password: TestDoctor123!")
    print(f"Role: {user.role}")
    print(f"Hospital: {user.hospital.name if user.hospital else 'None'}")
    print(f"Hospital ID: {user.hospital.id if user.hospital else 'None'}")
    print(f"Specialization: Internal Medicine")
    print(f"Registration: {reg_number}")
    print(f"Application Status: {app.status}")
    print("="*60)
    
    return user, app

if __name__ == '__main__':
    register_test_doctor()
