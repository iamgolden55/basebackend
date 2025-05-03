import os
import django
import sys
from datetime import datetime, timedelta
import pytz

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.user.custom_user import CustomUser
from api.models.medical.appointment import Appointment
from api.utils.email import send_appointment_confirmation_email

def test_email():
    """Test sending a confirmation email for an existing appointment"""
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
            
            # Send confirmation email
            email_sent = send_appointment_confirmation_email(appointment)
            print(f"Email sent: {email_sent}")
        else:
            print("No appointments found in the database.")
    
    except Exception as e:
        print(f"Error testing email: {str(e)}")

if __name__ == "__main__":
    test_email() 