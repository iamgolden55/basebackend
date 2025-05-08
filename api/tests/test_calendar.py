import os
import django
import sys
from datetime import datetime, timedelta
import pytz

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical.appointment import Appointment
from api.utils.calendar import generate_ics_for_appointment
from api.utils.email import send_appointment_confirmation_email

def test_calendar_attachment():
    """Test generating a calendar file for an appointment and sending it via email"""
    try:
        # Find an existing appointment
        appointment = Appointment.objects.filter(status='pending').first()
        
        if not appointment:
            print("No pending appointments found. Looking for any appointment...")
            appointment = Appointment.objects.first()
            
        if appointment:
            print(f"Found appointment: {appointment.appointment_id}")
            print(f"Patient: {appointment.patient.email}")
            print(f"Doctor: {appointment.doctor.full_name}")
            print(f"Date: {appointment.appointment_date}")
            
            # Generate calendar file
            try:
                ics_content = generate_ics_for_appointment(appointment)
                print(f"Successfully generated calendar file ({len(ics_content)} bytes)")
                
                # Save the calendar file for inspection
                with open(f"appointment_{appointment.appointment_id}.ics", "wb") as f:
                    f.write(ics_content)
                print(f"Saved calendar file to appointment_{appointment.appointment_id}.ics")
                
                # Send email with calendar attachment
                email_sent = send_appointment_confirmation_email(appointment)
                print(f"Email with calendar attachment sent: {email_sent}")
                
            except Exception as e:
                print(f"Error generating calendar file: {str(e)}")
        else:
            print("No appointments found in the database.")
    
    except Exception as e:
        print(f"Error testing calendar: {str(e)}")

if __name__ == "__main__":
    test_calendar_attachment() 