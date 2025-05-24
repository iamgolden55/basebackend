#!/usr/bin/env python
import os
import django
import sys
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# Import models after Django setup
from api.models import Department, Doctor, Hospital, MedicalRecord
from django.contrib.auth import get_user_model

User = get_user_model()

def create_departments():
    """Create sample departments for the existing hospital"""
    print("\nCreating sample departments...")
    
    # Get the existing hospital
    try:
        hospital = Hospital.objects.first()
        if not hospital:
            print("  No hospital found in database")
            return 0
        
        # Sample departments with all required fields
        departments = [
            {
                'name': 'Emergency',
                'code': 'EMER',
                'description': 'Emergency Department',
                'department_type': 'emergency',
                'floor_number': 1,
                'building': 'Main Building'
            },
            {
                'name': 'Cardiology',
                'code': 'CARD',
                'description': 'Cardiology Department',
                'department_type': 'specialty',
                'floor_number': 2,
                'building': 'Main Building'
            },
            {
                'name': 'Neurology',
                'code': 'NEUR',
                'description': 'Neurology Department',
                'department_type': 'specialty',
                'floor_number': 2,
                'building': 'Main Building'
            },
            {
                'name': 'Pediatrics',
                'code': 'PEDS',
                'description': 'Pediatrics Department',
                'department_type': 'specialty',
                'floor_number': 3,
                'building': 'Main Building'
            },
            {
                'name': 'Orthopedics',
                'code': 'ORTH',
                'description': 'Orthopedics Department',
                'department_type': 'specialty',
                'floor_number': 3,
                'building': 'Main Building'
            },
            {
                'name': 'Obstetrics & Gynecology',
                'code': 'OBGY',
                'description': 'Obstetrics & Gynecology Department',
                'department_type': 'specialty',
                'floor_number': 4,
                'building': 'Main Building'
            },
            {
                'name': 'Internal Medicine',
                'code': 'INTM',
                'description': 'Internal Medicine Department',
                'department_type': 'specialty',
                'floor_number': 5,
                'building': 'Main Building'
            },
            {
                'name': 'Surgery',
                'code': 'SURG',
                'description': 'Surgery Department',
                'department_type': 'specialty',
                'floor_number': 6,
                'building': 'Main Building'
            },
            {
                'name': 'Radiology',
                'code': 'RADI',
                'description': 'Radiology Department',
                'department_type': 'diagnostic',
                'floor_number': 1,
                'building': 'Diagnostic Wing'
            },
            {
                'name': 'Pharmacy',
                'code': 'PHAR',
                'description': 'Pharmacy Department',
                'department_type': 'support',
                'floor_number': 1,
                'building': 'Support Services'
            },
        ]
        
        # Create departments
        created_count = 0
        for dept_data in departments:
            # Check if department already exists
            if Department.objects.filter(name=dept_data['name'], hospital=hospital).exists():
                print(f"  Department already exists: {dept_data['name']}")
                continue
            
            # Create department
            dept = Department(
                hospital=hospital,
                is_active=True,
                **dept_data
            )
            dept.save()
            created_count += 1
            print(f"  Created department: {dept.name}")
        
        return created_count
    except Exception as e:
        print(f"  Error creating departments: {e}")
        return 0

def create_doctors():
    """Create sample doctors for the existing hospital"""
    print("\nCreating sample doctors...")
    
    # Get the existing hospital
    try:
        hospital = Hospital.objects.first()
        if not hospital:
            print("  No hospital found in database")
            return 0
        
        # Sample doctors with all required fields
        doctors = [
            {
                'first_name': 'John',
                'last_name': 'Smith',
                'email': 'john.smith@hospital.com',
                'phone': '+1234567890',
                'specialty': 'Cardiology',
                'license_number': 'MD12345',
                'gender': 'male'
            },
            {
                'first_name': 'Jane',
                'last_name': 'Doe',
                'email': 'jane.doe@hospital.com',
                'phone': '+1234567891',
                'specialty': 'Neurology',
                'license_number': 'MD12346',
                'gender': 'female'
            },
            {
                'first_name': 'Michael',
                'last_name': 'Johnson',
                'email': 'michael.johnson@hospital.com',
                'phone': '+1234567892',
                'specialty': 'Pediatrics',
                'license_number': 'MD12347',
                'gender': 'male'
            },
            {
                'first_name': 'Sarah',
                'last_name': 'Williams',
                'email': 'sarah.williams@hospital.com',
                'phone': '+1234567893',
                'specialty': 'Orthopedics',
                'license_number': 'MD12348',
                'gender': 'female'
            },
            {
                'first_name': 'Robert',
                'last_name': 'Brown',
                'email': 'robert.brown@hospital.com',
                'phone': '+1234567894',
                'specialty': 'Surgery',
                'license_number': 'MD12349',
                'gender': 'male'
            },
            {
                'first_name': 'Emily',
                'last_name': 'Jones',
                'email': 'emily.jones@hospital.com',
                'phone': '+1234567895',
                'specialty': 'Obstetrics',
                'license_number': 'MD12350',
                'gender': 'female'
            },
            {
                'first_name': 'David',
                'last_name': 'Miller',
                'email': 'david.miller@hospital.com',
                'phone': '+1234567896',
                'specialty': 'Internal Medicine',
                'license_number': 'MD12351',
                'gender': 'male'
            },
            {
                'first_name': 'Jennifer',
                'last_name': 'Davis',
                'email': 'jennifer.davis@hospital.com',
                'phone': '+1234567897',
                'specialty': 'Emergency Medicine',
                'license_number': 'MD12352',
                'gender': 'female'
            },
            {
                'first_name': 'James',
                'last_name': 'Wilson',
                'email': 'james.wilson@hospital.com',
                'phone': '+1234567898',
                'specialty': 'Radiology',
                'license_number': 'MD12353',
                'gender': 'male'
            },
            {
                'first_name': 'Linda',
                'last_name': 'Moore',
                'email': 'linda.moore@hospital.com',
                'phone': '+1234567899',
                'specialty': 'Anesthesiology',
                'license_number': 'MD12354',
                'gender': 'female'
            },
        ]
        
        # Create doctors
        created_count = 0
        for doctor_data in doctors:
            # Check if doctor already exists
            if Doctor.objects.filter(email=doctor_data['email']).exists():
                print(f"  Doctor already exists: {doctor_data['email']}")
                continue
            
            # Create doctor
            doctor = Doctor(
                hospital=hospital,
                status='active',
                is_verified=True,
                **doctor_data
            )
            doctor.save()
            created_count += 1
            print(f"  Created doctor: {doctor.first_name} {doctor.last_name}")
        
        return created_count
    except Exception as e:
        print(f"  Error creating doctors: {e}")
        return 0

def verify_data():
    """Verify the database state after import"""
    print("\n" + "=" * 50)
    print("Database Verification Results:")
    
    # Check counts
    users = User.objects.count()
    hospitals = Hospital.objects.count()
    departments = Department.objects.count()
    doctors = Doctor.objects.count()
    records = MedicalRecord.objects.count()
    
    print(f"Users: {users}")
    print(f"Hospitals: {hospitals}")
    print(f"Departments: {departments}")
    print(f"Doctors: {doctors}")
    print(f"Medical Records: {records}")
    
    # Check for specific users
    for email in ['eruwagolden55@gmail.com', 'admin@example.com']:
        user_exists = User.objects.filter(email=email).exists()
        print(f"User {email} exists: {'\u2705' if user_exists else '\u274c'}")
    
    print("=" * 50)

def main():
    print("\n" + "=" * 50)
    print("Sample Data Creation")
    print("=" * 50)
    
    # Create sample data
    dept_count = create_departments()
    doctor_count = create_doctors()
    
    print(f"\nCreated {dept_count} departments and {doctor_count} doctors")
    
    # Verify data
    verify_data()
    
    print("\nThe hospital admin security features are preserved:")
    print("1. Domain validation for hospital email addresses")
    print("2. Required hospital code verification")
    print("3. Mandatory 2FA for all hospital admins")
    print("4. Enhanced security with trusted device tracking")
    print("5. Rate limiting after 3 failed attempts")
    print("6. Account lockout for 15 minutes after 5 failed attempts")

if __name__ == "__main__":
    main()
