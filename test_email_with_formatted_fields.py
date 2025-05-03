"""
Test the appointment confirmation email with new formatted fields.
This script should be run with: python manage.py shell < test_email_with_formatted_fields.py
"""

from api.models.user.custom_user import CustomUser
from api.models.medical.appointment import Appointment
from api.utils.email import send_appointment_confirmation_email
import json

def print_separator():
    print("\n" + "="*80 + "\n")

def test_email_confirmation():
    # Find Al-Amin's user account
    user = CustomUser.objects.get(id=48)  # Al-Amin's user ID
    print(f"User: {user.first_name} {user.last_name} ({user.email})")
    
    # Get all of Al-Amin's appointments
    appointments = Appointment.objects.filter(patient=user).select_related(
        'doctor', 'doctor__user', 'hospital', 'department'
    ).order_by('appointment_date')
    
    print(f"Found {appointments.count()} appointments")
    print_separator()
    
    # List basic appointment info
    for i, appt in enumerate(appointments, 1):
        print(f"{i}. {appt.appointment_date.strftime('%Y-%m-%d %H:%M')} - "\
              f"{appt.department.name} with Dr. {appt.doctor.user.first_name} {appt.doctor.user.last_name} "\
              f"(ID: {appt.id}, Ref: {appt.appointment_id})")
    
    print_separator()
    
    # Choose one appointment to test
    if appointments.exists():
        # Select one appointment for email testing
        test_appointment = appointments.first()
        print(f"Testing email confirmation for appointment {test_appointment.id} (Ref: {test_appointment.appointment_id})")
        
        # Confirm with user before sending email
        confirm = input("Send a test email confirmation? (y/n): ")
        if confirm.lower() == 'y':
            print(f"Sending test email to {user.email}...")
            success = send_appointment_confirmation_email(test_appointment)
            if success:
                print("Email sent successfully!")
            else:
                print("Failed to send email.")
        else:
            print("Email sending canceled.")
            
            # Just print what would be sent
            print("\nEmail data that would be sent:")
            from api.serializers import AppointmentSerializer
            serializer = AppointmentSerializer(test_appointment)
            serializer_data = serializer.data
            
            email_context = {
                'patient_name': serializer_data.get('patient_name'),
                'appointment_id': test_appointment.appointment_id,
                'doctor_name': serializer_data.get('doctor_full_name'),
                'department_name': serializer_data.get('department_name'),
                'hospital_name': serializer_data.get('hospital_name'),
                'appointment_date': serializer_data.get('formatted_date_time'),
                'appointment_date_only': serializer_data.get('formatted_date'),
                'appointment_time_only': serializer_data.get('formatted_time'),
                'is_insurance_based': test_appointment.is_insurance_based,
                'payment_status': test_appointment.payment_status,
                'appointment_type': serializer_data.get('formatted_appointment_type'),
                'priority': serializer_data.get('formatted_priority'),
                'chief_complaint': test_appointment.chief_complaint,
                'calendar_link_included': True,
                'important_notes': serializer_data.get('important_notes'),
                'duration': serializer_data.get('appointment_duration_display')
            }
            
            print(json.dumps(email_context, indent=2, default=str))
    else:
        print("No appointments found for testing.")

# Run the test
print_separator()
print("APPOINTMENT EMAIL CONFIRMATION TEST")
print_separator()
test_email_confirmation() 