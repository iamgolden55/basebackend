from api.models.user.custom_user import CustomUser
from api.models.medical.department import Department
from api.models.medical.hospital import Hospital
from api.models.medical_staff.doctor import Doctor
from api.models.medical.appointment import Appointment
from datetime import datetime
import pytz
import uuid

# Get the user
user = CustomUser.objects.get(id=48)
print(f'User: {user.email}')

# Get the hospital
hospital = Hospital.objects.get(id=3)
print(f'Hospital: {hospital.name}')

# Get the department
department = Department.objects.get(id=14)
print(f'Department: {department.name}')

# Get the doctor
doctors = Doctor.objects.filter(department=department, hospital=hospital)
if doctors.exists():
    doctor = doctors.first()
    print(f'Doctor: {doctor.full_name} (ID: {doctor.id})')
    
    # Create appointment for May 7, 2025 at 10:00 AM
    appointment_date = datetime(2025, 5, 7, 10, 0, 0, tzinfo=pytz.UTC)
    
    # Check doctor availability
    if doctor.is_available_at(appointment_date):
        print(f'Doctor is available at {appointment_date}')
        
        try:
            # Generate a unique appointment ID
            appointment_id = f"APT-{str(uuid.uuid4())[:8].upper()}"
            
            appointment = Appointment.objects.create(
                appointment_id=appointment_id,
                patient=user,
                doctor=doctor,
                hospital=hospital,
                department=department,
                appointment_date=appointment_date,
                appointment_type='first_visit',
                priority='normal',
                chief_complaint='General checkup',
                notes='Appointment created via script',
                payment_required=False,
                payment_status='waived',
                duration=30
            )
            print(f'Successfully created appointment on {appointment.appointment_date}')
            print(f'Appointment ID: {appointment.id}')
            print(f'Appointment Reference: {appointment.appointment_id}')
            
            # Send confirmation email manually
            from api.utils.email import send_appointment_confirmation_email
            email_sent = send_appointment_confirmation_email(appointment)
            print(f'Confirmation email sent: {email_sent}')
            
        except Exception as e:
            print(f'Error creating appointment: {str(e)}')
    else:
        print(f'Doctor is not available at {appointment_date}')
else:
    print('No doctors found in this department') 