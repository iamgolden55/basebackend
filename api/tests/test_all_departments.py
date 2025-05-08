from api.models.user.custom_user import CustomUser
from api.models.medical.department import Department
from api.models.medical.hospital import Hospital
from api.models.medical_staff.doctor import Doctor
from api.models.medical.appointment import Appointment
from datetime import datetime, timedelta
import pytz
import uuid

def test_department(department_id):
    """Test appointment creation for a specific department"""
    # Get the user (Al-Amin)
    user = CustomUser.objects.get(id=48)
    print(f'User: {user.email}')

    # Get Abuja Central Hospital
    hospital = Hospital.objects.get(id=3)
    print(f'Hospital: {hospital.name}')

    # Get the department
    department = Department.objects.get(id=department_id)
    print(f'\nTesting Department: {department.name} (ID: {department_id})')

    # Get doctors in this department
    doctors = Doctor.objects.filter(department=department, hospital=hospital)
    if not doctors.exists():
        print(f'No doctors found in {department.name} department')
        return False
    
    # Get the first doctor
    doctor = doctors.first()
    print(f'Doctor: {doctor.full_name} (ID: {doctor.id})')
    print(f'Consultation days: {doctor.consultation_days}')
    print(f'Consultation hours: {doctor.consultation_hours_start} - {doctor.consultation_hours_end}')
    
    # Create appointment for next week at 10:00 AM
    now = datetime.now(pytz.UTC)
    # Find a future day (within 7 days) that works with the doctor's schedule
    appointment_date = None
    for i in range(1, 8):
        test_date = now + timedelta(days=i)
        test_date = test_date.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # Get the 3-letter day name
        day_name = test_date.strftime('%a')
        print(f'Testing {day_name} ({test_date.strftime("%Y-%m-%d")})')
        
        # Check if doctor works on this day (flexible check)
        if doctor.consultation_days:
            consultation_days = [d.strip() for d in doctor.consultation_days.split(',')]
            day_matches = any(day.lower() in day_name.lower() for day in consultation_days) or \
                         any(day_name.lower() in day.lower() for day in consultation_days) or \
                         day_name in consultation_days
        else:
            day_matches = True
        
        if day_matches:
            appointment_date = test_date
            print(f'Found matching day: {day_name}')
            break
    
    if not appointment_date:
        print('Could not find a suitable day for appointment')
        return False
    
    # Check doctor availability
    is_available = True
    conflicting = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appointment_date,
        status__in=['pending', 'confirmed', 'in_progress', 'scheduled', 'checking_in']
    ).exists()
    
    if conflicting:
        print(f'Doctor has conflicting appointment at {appointment_date}')
        is_available = False
    
    # Check consultation hours
    if doctor.consultation_hours_start and doctor.consultation_hours_end:
        appointment_time = appointment_date.time()
        if not (doctor.consultation_hours_start <= appointment_time <= doctor.consultation_hours_end):
            print(f'Appointment time {appointment_time} is outside doctor hours')
            is_available = False
    
    if is_available:
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
                chief_complaint=f'Test appointment for {department.name} department',
                notes='Appointment created via test script',
                payment_required=False,
                payment_status='waived',
                duration=30
            )
            print(f'SUCCESS: Created appointment on {appointment.appointment_date}')
            print(f'Appointment ID: {appointment.id}')
            print(f'Appointment Reference: {appointment.appointment_id}')
            
            # Send confirmation email manually
            from api.utils.email import send_appointment_confirmation_email
            try:
                email_sent = send_appointment_confirmation_email(appointment)
                print(f'Confirmation email sent: {email_sent}')
            except Exception as e:
                print(f'Error sending email: {str(e)}')
            
            return True
        except Exception as e:
            print(f'Error creating appointment: {str(e)}')
            return False
    else:
        print(f'Doctor is not available at {appointment_date}')
        return False


# Test all departments at Abuja Central Hospital
print("====== TESTING ALL DEPARTMENTS FOR APPOINTMENT BOOKING ======")

# Get all departments at Abuja Central Hospital (ID 3)
hospital = Hospital.objects.get(id=3)
departments = Department.objects.filter(
    id__in=Doctor.objects.filter(hospital=hospital).values_list('department_id', flat=True).distinct()
)

print(f"Found {departments.count()} departments with doctors at {hospital.name}")

# Test each department
successful_departments = []
failed_departments = []

for dept in departments:
    print("\n" + "="*50)
    print(f"Testing department: {dept.name} (ID: {dept.id})")
    
    success = test_department(dept.id)
    if success:
        successful_departments.append(dept.name)
    else:
        failed_departments.append(dept.name)

# Print summary
print("\n\n" + "="*50)
print("APPOINTMENT TESTING SUMMARY")
print("="*50)
print(f"Successfully booked appointments in {len(successful_departments)} departments:")
for dept in successful_departments:
    print(f"- {dept}")

if failed_departments:
    print(f"\nFailed to book appointments in {len(failed_departments)} departments:")
    for dept in failed_departments:
        print(f"- {dept}")
else:
    print("\nAll departments passed the test!") 