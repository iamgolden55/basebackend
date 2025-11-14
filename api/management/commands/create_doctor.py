"""
Management command to create a doctor with both CustomUser and Doctor records.

This ensures that doctors have both authentication (CustomUser) and professional (Doctor) records.

Usage:
    python manage.py create_doctor \
        --email dr.example@hospital.com \
        --password SecurePassword123! \
        --first-name John \
        --last-name Doe \
        --hospital-id 27 \
        --department-id 32 \
        --specialization "General Medicine" \
        --phone "+2348012345678"
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from datetime import date, timedelta
from api.models.user.custom_user import CustomUser
from api.models.medical_staff.doctor import Doctor
from api.models.medical.hospital import Hospital
from api.models.medical.department import Department


class Command(BaseCommand):
    help = 'Create a doctor with both CustomUser and Doctor model records'

    def add_arguments(self, parser):
        # Required arguments
        parser.add_argument('--email', type=str, required=True, help='Doctor email address')
        parser.add_argument('--password', type=str, required=True, help='Doctor password')
        parser.add_argument('--first-name', type=str, required=True, help='First name')
        parser.add_argument('--last-name', type=str, required=True, help='Last name')
        parser.add_argument('--hospital-id', type=int, required=True, help='Hospital ID')
        parser.add_argument('--department-id', type=int, required=True, help='Department ID')
        parser.add_argument('--specialization', type=str, required=True, help='Medical specialization')

        # Optional arguments
        parser.add_argument('--phone', type=str, default='+2348000000000', help='Phone number')
        parser.add_argument('--country', type=str, default='Nigeria', help='Country')
        parser.add_argument('--state', type=str, default='Delta', help='State')
        parser.add_argument('--city', type=str, default='Asaba', help='City')
        parser.add_argument('--years-experience', type=int, default=5, help='Years of experience')
        parser.add_argument('--skip-otp', action='store_true', help='Disable OTP for this doctor')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        hospital_id = options['hospital_id']
        department_id = options['department_id']
        specialization = options['specialization']
        phone = options['phone']
        country = options['country']
        state = options['state']
        city = options['city']
        years_experience = options['years_experience']
        skip_otp = options['skip_otp']

        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists():
            raise CommandError(f'User with email {email} already exists')

        # Verify hospital exists
        try:
            hospital = Hospital.objects.get(id=hospital_id)
        except Hospital.DoesNotExist:
            raise CommandError(f'Hospital with ID {hospital_id} does not exist')

        # Verify department exists
        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            raise CommandError(f'Department with ID {department_id} does not exist')

        # Verify department belongs to hospital
        if department.hospital_id != hospital_id:
            raise CommandError(
                f'Department {department.name} does not belong to hospital {hospital.name}'
            )

        try:
            with transaction.atomic():
                # Step 1: Create CustomUser record
                self.stdout.write('Creating CustomUser record...')
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role='doctor',
                    phone=phone,
                    country=country,
                    state=state,
                    city=city,
                    is_email_verified=True,  # Auto-verify for staff
                    has_completed_onboarding=True,
                    otp_required_for_login=not skip_otp  # Enable/disable OTP
                )
                self.stdout.write(self.style.SUCCESS(f'✓ Created CustomUser (ID: {user.id})'))

                # Step 2: Create Doctor record
                self.stdout.write('Creating Doctor record...')
                doctor = Doctor.objects.create(
                    user=user,
                    hospital=hospital,
                    department=department,
                    specialization=specialization,
                    medical_license_number=f'MD-{user.id}-NG-{date.today().year}',
                    license_expiry_date=date.today() + timedelta(days=1825),  # 5 years
                    years_of_experience=years_experience,
                    qualifications=['MBBS', f'MD {specialization}'],
                    is_active=True,
                    status='active',
                    available_for_appointments=True,
                    consultation_days='Mon,Tue,Wed,Thu,Fri',
                    max_daily_appointments=20,
                    appointment_duration=30
                )
                self.stdout.write(self.style.SUCCESS(f'✓ Created Doctor record (ID: {doctor.id})'))

                # Success summary
                self.stdout.write(self.style.SUCCESS('\n' + '='*60))
                self.stdout.write(self.style.SUCCESS('✓ Doctor created successfully!'))
                self.stdout.write(self.style.SUCCESS('='*60))
                self.stdout.write(f'\nLogin Credentials:')
                self.stdout.write(f'  Email: {email}')
                self.stdout.write(f'  Password: {password}')
                self.stdout.write(f'  OTP Required: {"No" if skip_otp else "Yes"}')
                self.stdout.write(f'\nProfessional Details:')
                self.stdout.write(f'  Name: {first_name} {last_name}')
                self.stdout.write(f'  Hospital: {hospital.name}')
                self.stdout.write(f'  Department: {department.name}')
                self.stdout.write(f'  Specialization: {specialization}')
                self.stdout.write(f'  License: {doctor.medical_license_number}')
                self.stdout.write(f'  Experience: {years_experience} years')
                self.stdout.write(f'\nUser ID: {user.id}')
                self.stdout.write(f'Doctor ID: {doctor.id}')
                self.stdout.write('')

        except Exception as e:
            raise CommandError(f'Failed to create doctor: {str(e)}')
