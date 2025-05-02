from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from api.models.medical.appointment import AppointmentType, Appointment
from api.models.medical.department import Department
from api.models.medical.hospital_auth import Hospital
from api.models.medical_staff.doctor import Doctor
import random
import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test doctors, availabilities, and appointments for frontend testing'

    def handle(self, *args, **options):
        # Create a default hospital if none exists
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
        
        # Get all departments
        departments = Department.objects.all()
        if not departments.exists():
            self.stdout.write(self.style.ERROR('No departments found. Please run loaddata or create departments first.'))
            return
            
        # Get all appointment types
        appointment_types = AppointmentType.objects.all()
        if not appointment_types.exists():
            self.stdout.write(self.style.ERROR('No appointment types found. Please run create_default_appointment_types first.'))
            return
            
        # Create test doctors for each department
        doctors_created = 0
        
        specialties = [
            'Cardiology', 'Dermatology', 'Neurology', 'Orthopedics', 
            'Pediatrics', 'Psychiatry', 'Oncology', 'Gynecology',
            'Urology', 'Ophthalmology', 'ENT', 'Internal Medicine'
        ]
        
        languages = ['English', 'Spanish', 'French', 'Mandarin', 'Arabic', 'Hindi', 'Portuguese', 'Russian', 'Japanese']
        
        # Create 3 doctors per department
        for department in departments:
            for i in range(3):
                # Create user for doctor
                username = f"dr_{department.name.lower().replace(' ', '')}_{i+1}"
                email = f"{username}@hospital.com"
                
                user, user_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': f"Doctor{i+1}",
                        'last_name': f"{department.name[:5]}",
                        'is_staff': True
                    }
                )
                
                if user_created:
                    user.set_password('password123')
                    user.save()
                
                # Generate a medical license number
                license_number = f"ML{random.randint(100000, 999999)}"
                
                # Create a random license expiry date (1-5 years in the future)
                expiry_date = timezone.now().date() + datetime.timedelta(days=random.randint(365, 1825))
                
                # Create or get doctor
                doctor, doc_created = Doctor.objects.get_or_create(
                    user=user,
                    defaults={
                        'specialization': random.choice(specialties),
                        'department': department,
                        'hospital': hospital,
                        'languages_spoken': ','.join(random.sample(languages, k=random.randint(1, 3))),
                        'years_of_experience': random.randint(1, 30),
                        'medical_license_number': license_number,
                        'license_expiry_date': expiry_date,
                        'consultation_days': 'Mon,Tue,Wed,Thu,Fri',
                        'max_daily_appointments': 20,
                        'appointment_duration': 30,
                        'qualifications': ['MD', 'Board Certified'],
                        'consultation_hours_start': datetime.time(9, 0),
                        'consultation_hours_end': datetime.time(17, 0),
                    }
                )
                
                if doc_created:
                    doctors_created += 1
                    
        self.stdout.write(self.style.SUCCESS(f'Created {doctors_created} test doctors'))
        
        # Create test patients
        patients_created = 0
        for i in range(10):
            username = f"patient_{i+1}"
            email = f"{username}@example.com"
            
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f"Patient{i+1}",
                    'last_name': f"Test",
                    'is_staff': False
                }
            )
            
            if user_created:
                user.set_password('password123')
                user.save()
                patients_created += 1
                
        self.stdout.write(self.style.SUCCESS(f'Created {patients_created} test patients'))
        
        # Create test appointments (some past, some future)
        today = timezone.now().date()
        
        # Delete any existing future appointments to avoid conflicts
        Appointment.objects.filter(appointment_date__gte=today).delete()
        
        # Create appointments spread over the next 30 days
        appointments_created = 0
        doctors = Doctor.objects.all()
        patients = User.objects.filter(username__startswith='patient_')
        
        if not patients.exists():
            self.stdout.write(self.style.ERROR('No patient users found. Check patient creation above.'))
            return
            
        # For each day in the next 30 days
        for day_offset in range(30):
            appointment_date = today + datetime.timedelta(days=day_offset)
            
            # For each time slot (9am to 4pm, every hour)
            for hour in range(9, 17):
                # Only create appointments for some slots (random)
                if random.random() < 0.4:  # 40% chance to create an appointment for each slot
                    appointment_datetime = datetime.datetime.combine(
                        appointment_date,
                        datetime.time(hour, 0),
                        tzinfo=timezone.get_current_timezone()
                    )
                    
                    # Choose random doctor and patient
                    doctor = random.choice(doctors)
                    patient = random.choice(patients)
                    appointment_type = random.choice(appointment_types)
                    
                    # Create appointment
                    try:
                        appointment = Appointment.objects.create(
                            patient=patient,
                            doctor=doctor,
                            hospital=hospital,
                            department=doctor.department,
                            appointment_type=appointment_type.id,
                            priority=random.choice(['normal', 'priority', 'emergency']),
                            appointment_date=appointment_datetime,
                            chief_complaint=f"Test complaint for {appointment_type.name}",
                            status=random.choice(['scheduled', 'confirmed', 'checking_in'])
                        )
                        
                        appointments_created += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'Error creating appointment: {str(e)}'))
                    
        self.stdout.write(self.style.SUCCESS(f'Created {appointments_created} test appointments'))
        
        self.stdout.write(self.style.SUCCESS('All test data created successfully! You can now test the appointment booking flow.')) 