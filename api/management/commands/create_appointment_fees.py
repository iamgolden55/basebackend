from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models.medical.hospital_auth import Hospital
from api.models.medical.department import Department
from api.models.medical_staff.doctor import Doctor
from api.models.medical.appointment_fee import AppointmentFee
import random

class Command(BaseCommand):
    help = 'Creates default appointment fees for departments and doctors'

    def handle(self, *args, **options):
        # Get default hospital
        try:
            hospital = Hospital.objects.get(name="General Hospital")
        except Hospital.DoesNotExist:
            self.stdout.write(self.style.ERROR('Default hospital not found. Please run create_test_departments first.'))
            return
        
        # Get all departments
        departments = Department.objects.all()
        if not departments.exists():
            self.stdout.write(self.style.ERROR('No departments found. Please run create_test_departments first.'))
            return
        
        # Get all doctors
        doctors = Doctor.objects.all()
        if not doctors.exists():
            self.stdout.write(self.style.ERROR('No doctors found. Please run create_appointment_availability first to create doctors.'))
            return
        
        # Create fee types
        fee_types = [
            'general', 'specialist', 'emergency', 'follow_up', 'video'
        ]
        
        # Set current date for validity
        current_date = timezone.now().date()
        # Valid for 1 year
        valid_until = current_date.replace(year=current_date.year + 1)
        
        fees_created = 0
        
        # Create department-level fees
        for department in departments:
            for fee_type in fee_types:
                # Skip if this fee type already exists for this department
                if AppointmentFee.objects.filter(
                    hospital=hospital,
                    department=department,
                    doctor=None,
                    fee_type=fee_type,
                    is_active=True
                ).exists():
                    self.stdout.write(self.style.SUCCESS(f'Fee already exists for {department.name} ({fee_type})'))
                    continue
                    
                # Base fee varies by department and fee type
                if fee_type == 'emergency':
                    base_fee = random.randint(150, 300)
                elif fee_type == 'specialist':
                    base_fee = random.randint(100, 200)
                elif fee_type == 'video':
                    base_fee = random.randint(50, 100)
                elif fee_type == 'follow_up':
                    base_fee = random.randint(30, 80)
                else:  # general
                    base_fee = random.randint(50, 120)
                
                try:
                    fee = AppointmentFee.objects.create(
                        hospital=hospital,
                        department=department,
                        doctor=None,  # Department-level fee
                        fee_type=fee_type,
                        base_fee=base_fee,
                        currency='NGN',
                        registration_fee=random.choice([0, 10, 20]),
                        medical_card_fee=random.choice([0, 5, 10]),
                        insurance_coverage_percentage=random.choice([0, 50, 70, 80]),
                        senior_citizen_discount=random.choice([0, 10, 20]),
                        valid_from=current_date,
                        valid_until=valid_until,
                        is_active=True
                    )
                    fees_created += 1
                    self.stdout.write(self.style.SUCCESS(f'Created department fee: {fee}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating fee for {department.name} ({fee_type}): {str(e)}'))
        
        # Create doctor-specific fees (only for a few top doctors)
        for doctor in doctors[:min(len(doctors), 5)]:  # Only for the first 5 doctors
            for fee_type in ['specialist', 'video']:  # Only specific fee types
                # Skip if this fee type already exists for this doctor
                if AppointmentFee.objects.filter(
                    hospital=hospital,
                    department=doctor.department,
                    doctor=doctor,
                    fee_type=fee_type,
                    is_active=True
                ).exists():
                    self.stdout.write(self.style.SUCCESS(f'Fee already exists for doctor {doctor.user.get_full_name()} ({fee_type})'))
                    continue
                    
                # Higher fees for specific doctors
                if fee_type == 'specialist':
                    base_fee = random.randint(150, 250)
                else:  # video
                    base_fee = random.randint(80, 150)
                
                try:
                    fee = AppointmentFee.objects.create(
                        hospital=hospital,
                        department=doctor.department,
                        doctor=doctor,
                        fee_type=fee_type,
                        base_fee=base_fee,
                        currency='NGN',
                        registration_fee=random.choice([0, 10, 20]),
                        medical_card_fee=random.choice([0, 5, 10]),
                        insurance_coverage_percentage=random.choice([0, 50, 70, 80]),
                        senior_citizen_discount=random.choice([0, 10, 20]),
                        valid_from=current_date,
                        valid_until=valid_until,
                        is_active=True
                    )
                    fees_created += 1
                    self.stdout.write(self.style.SUCCESS(f'Created doctor fee: {fee}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating fee for doctor {doctor.user.get_full_name()} ({fee_type}): {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Created {fees_created} appointment fees')) 