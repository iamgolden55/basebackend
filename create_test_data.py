from django.contrib.auth import get_user_model
from api.models import Hospital, Department, Doctor, CustomUser

def create_test_data():
    print("🏗️ Creating test data...")

    # Create test hospital
    hospital, created = Hospital.objects.get_or_create(
        name="Test Hospital",
        defaults={
            'address': "123 Test Street",
            'city': "Test City",
            'state': "Test State",
            'country': "Test Country",
            'phone': "1234567890"
        }
    )
    print(f"{'✨ Created' if created else '✅ Found'} hospital: {hospital.name} (ID: {hospital.id})")

    # Create test department
    department, created = Department.objects.get_or_create(
        name="General Medicine",
        hospital=hospital
    )
    print(f"{'✨ Created' if created else '✅ Found'} department: {department.name} (ID: {department.id})")

    # Create test patient
    User = get_user_model()
    patient, created = User.objects.get_or_create(
        email="testpatient@example.com",
        defaults={
            'first_name': "Test",
            'last_name': "Patient",
            'role': 'patient',
            'is_email_verified': True
        }
    )
    if created:
        patient.set_password("testpassword123")
        patient.save()
        print("✨ Created new patient")
    else:
        # Update password anyway to ensure it's correct
        patient.set_password("testpassword123")
        patient.save()
        print("✅ Found existing patient, updated password")
    
    print(f"Patient details:")
    print(f"- Email: {patient.email}")
    print(f"- Role: {patient.role}")
    print(f"- Verified: {patient.is_email_verified}")

    # Create test doctor
    doctor_user, created = User.objects.get_or_create(
        email="testdoctor@example.com",
        defaults={
            'first_name': "Test",
            'last_name': "Doctor",
            'role': 'doctor',
            'is_email_verified': True
        }
    )
    if created:
        doctor_user.set_password("testpassword123")
        doctor_user.save()
        print("✨ Created new doctor user")
    else:
        # Update password anyway to ensure it's correct
        doctor_user.set_password("testpassword123")
        doctor_user.save()
        print("✅ Found existing doctor user, updated password")
    
    doctor, created = Doctor.objects.get_or_create(
        user=doctor_user,
        defaults={
            'department': department,
            'hospital': hospital,
            'specialization': "General Medicine",
            'license_number': "TEST123"
        }
    )
    print(f"{'✨ Created' if created else '✅ Found'} doctor profile")
    print(f"Doctor details:")
    print(f"- Email: {doctor_user.email}")
    print(f"- Role: {doctor_user.role}")
    print(f"- Verified: {doctor_user.is_email_verified}")
    print(f"- License: {doctor.license_number}")
    print(f"- Hospital: {doctor.hospital.name}")
    print(f"- Department: {doctor.department.name}")

    print("\n✅ Test data creation completed!")
    print("\nTest Credentials:")
    print("------------------")
    print("Patient Email: testpatient@example.com")
    print("Patient Password: testpassword123")
    print("Doctor Email: testdoctor@example.com")
    print("Doctor Password: testpassword123")

if __name__ == "__main__":
    create_test_data() 