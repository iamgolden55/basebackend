from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from api.models.medical.appointment import AppointmentType, Appointment
from api.models.medical.department import Department
from api.models.medical.hospital_auth import Hospital
from api.models.medical_staff.doctor import Doctor
from api.models.medical.appointment_fee import AppointmentFee
from api.models.medical.hospital_registration import HospitalRegistration
import random
import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates appointment availability for the next 30 days'

    def handle(self, *args, **options):
        # Get or create a default hospital
        hospital, created = Hospital.objects.get_or_create(
            name="General Hospital",
            defaults={
                'address': '123 Medical Drive',
                'city': 'Healthcare City',
                'state': 'Medical State',
                'zip_code': '12345',
                'country': 'United States',
                'phone': '555-123-4567',
                'email': 'info@generalhospital.com',
                'website': 'https://generalhospital.com'
            }
        )
        
        # Get existing departments
        departments = Department.objects.all()
        if not departments.exists():
            self.stdout.write(self.style.ERROR('No departments found. Cannot create doctors.'))
            return
        
        # Check for appointment types
        appointment_types = AppointmentType.objects.all()
        if not appointment_types.exists():
            self.stdout.write(self.style.ERROR('No appointment types found. Please run create_default_appointment_types first.'))
            return
            
        # Create sample users for test patients if they don't exist
        patients_created = 0
        for i in range(1, 6):
            username = f"patient_{i}"
            email = f"{username}@example.com"
            
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f"Patient{i}",
                    'last_name': f"Test",
                    'is_staff': False
                }
            )
            
            if user_created:
                user.set_password('password123')
                user.save()
                patients_created += 1
                
            # Register patient with hospital if not already registered
            registration, reg_created = HospitalRegistration.objects.get_or_create(
                user=user,
                hospital=hospital,
                defaults={
                    'created_at': timezone.now(),
                    'status': 'approved',
                    'is_primary': True,
                    'approved_date': timezone.now()
                }
            )
            
            if reg_created:
                self.stdout.write(self.style.SUCCESS(f'Registered patient {user.username} with hospital'))
        
        if patients_created > 0:
            self.stdout.write(self.style.SUCCESS(f'Created {patients_created} test patients'))
        else:
            self.stdout.write(self.style.SUCCESS('Using existing test patients'))
        
        # Create one doctor for each department if they don't exist
        doctors_created = 0
        doctors = []
        
        for department in departments:
            # Normalize department name for username
            dept_name = department.name.lower().replace(' ', '')
            username = f"dr_{dept_name}_1"
            email = f"{username}@hospital.com"
            
            # Create user for doctor
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f"Doctor",
                    'last_name': f"{department.name[:5]}",
                    'is_staff': True
                }
            )
            
            if user_created:
                user.set_password('password123')
                user.save()
                
            # Check if doctor exists
            doctor = None
            try:
                doctor = Doctor.objects.get(user=user)
                self.stdout.write(self.style.SUCCESS(f'Using existing doctor: {user.first_name} {user.last_name}'))
            except Doctor.DoesNotExist:
                # Generate a medical license number
                license_number = f"ML{random.randint(100000, 999999)}"
                
                # Create a random license expiry date (1-5 years in the future)
                expiry_date = timezone.now().date() + datetime.timedelta(days=random.randint(365, 1825))
                
                try:
                    # Create the doctor
                    doctor = Doctor.objects.create(
                        user=user,
                        specialization=department.name,
                        department=department,
                        hospital=hospital,
                        languages_spoken='English,Spanish',
                        years_of_experience=random.randint(5, 20),
                        medical_license_number=license_number,
                        license_expiry_date=expiry_date,
                        consultation_days='Mon,Tue,Wed,Thu,Fri',
                        max_daily_appointments=20,
                        appointment_duration=30,
                        qualifications=['MD', 'Board Certified'],
                        consultation_hours_start=datetime.time(9, 0),
                        consultation_hours_end=datetime.time(17, 0),
                    )
                    doctors_created += 1
                    self.stdout.write(self.style.SUCCESS(f'Created doctor: {user.first_name} {user.last_name}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating doctor for {department.name}: {str(e)}'))
                    continue
            
            if doctor:
                doctors.append(doctor)
        
        if doctors_created > 0:
            self.stdout.write(self.style.SUCCESS(f'Created {doctors_created} test doctors'))
        else:
            self.stdout.write(self.style.SUCCESS('Using existing doctors'))
            
        if not doctors:
            self.stdout.write(self.style.ERROR('No doctors available for creating appointments.'))
            return
            
        # Check if we have appointment fees
        fees = AppointmentFee.objects.all()
        if not fees.exists():
            self.stdout.write(self.style.ERROR('No appointment fees found. Please run create_appointment_fees first.'))
            return
        
        # Delete any future appointments for our doctors to avoid conflicts
        today = timezone.now().date()
        future_appointments = Appointment.objects.filter(
            appointment_date__date__gte=today,
            doctor__in=doctors
        )
        deleted_count = future_appointments.count()
        future_appointments.delete()
        self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing future appointments'))
        
        # Create appointments for the next 30 days
        appointment_count = 0
        today = timezone.now().date()
        
        # Get test patients
        patients = User.objects.filter(username__startswith='patient_')
        if not patients.exists():
            self.stdout.write(self.style.ERROR('No patient users found.'))
            return
        
        # For each day in the next 30 days
        for day_offset in range(30):
            appointment_date = today + datetime.timedelta(days=day_offset)
            
            # Skip weekends (5=Saturday, 6=Sunday)
            if appointment_date.weekday() >= 5:
                continue
            
            # For each doctor
            for doctor in doctors:
                # For each time slot (9am to 4pm, half-hour increments)
                for hour in range(9, 17):
                    for minute in [0, 30]:
                        # Only create empty slots with 80% probability to leave some availability
                        if random.random() < 0.2:
                            # Create appointment datetime
                            appointment_datetime = datetime.datetime.combine(
                                appointment_date,
                                datetime.time(hour, minute),
                                tzinfo=timezone.get_current_timezone()
                            )
                            
                            # Choose a random appointment type
                            appointment_type = random.choice(appointment_types)
                            fee_type = 'general'  # Default
                            
                            if appointment_type.id == 'follow_up':
                                fee_type = 'follow_up'
                            elif appointment_type.id == 'consultation':
                                fee_type = random.choice(['general', 'specialist'])
                            elif appointment_type.id == 'first_visit':
                                fee_type = random.choice(['general', 'specialist'])
                            
                            # Find an appropriate fee
                            fee = AppointmentFee.objects.filter(
                                hospital=hospital,
                                department=doctor.department,
                                fee_type=fee_type,
                                is_active=True
                            ).first()
                            
                            if not fee:
                                self.stdout.write(self.style.WARNING(f'No fee found for {doctor.department.name} {fee_type} appointment'))
                                continue
                            
                            # Choose a random patient
                            patient = random.choice(patients)
                            
                            # Create an appointment
                            try:
                                appointment = Appointment.objects.create(
                                    patient=patient,
                                    doctor=doctor,
                                    hospital=hospital,
                                    department=doctor.department,
                                    appointment_type=appointment_type.id,
                                    priority='normal',
                                    appointment_date=appointment_datetime,
                                    chief_complaint=f"Test appointment for {appointment_type.name}",
                                    status='confirmed',
                                    fee=fee
                                )
                                appointment_count += 1
                                self.stdout.write(self.style.SUCCESS(f'Created appointment: {appointment}'))
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f'Error creating appointment: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Created {appointment_count} test appointments'))
        self.stdout.write(self.style.SUCCESS('All test data created successfully! You can now test the appointment booking flow.')) 