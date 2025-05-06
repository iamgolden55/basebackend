#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# Now import Django models
from api.models import CustomUser, Appointment

def count_doctor_appointments():
    try:
        # Get the doctor user
        doctor_user = CustomUser.objects.get(email='eruwagolden@gmail.com')
        
        # Get all appointments for the doctor
        appointments = Appointment.objects.filter(doctor=doctor_user.doctor_profile)
        total_appointments = appointments.count()
        
        print(f"Dr. {doctor_user.first_name} {doctor_user.last_name} has {total_appointments} total appointments")
        
        # Count appointments by status
        print("\nAppointments by status:")
        for status in appointments.values_list('status', flat=True).distinct():
            count = appointments.filter(status=status).count()
            print(f"- {status}: {count}")
            
        # List upcoming appointments
        print("\nUpcoming appointments:")
        from django.utils import timezone
        upcoming = appointments.filter(appointment_date__gte=timezone.now()).order_by('appointment_date')
        for appt in upcoming:
            print(f"- {appt.appointment_id}: {appt.appointment_date.strftime('%Y-%m-%d %H:%M')} - {appt.patient.first_name} {appt.patient.last_name}")
            
    except CustomUser.DoesNotExist:
        print("Doctor with email eruwagolden@gmail.com not found.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    count_doctor_appointments() 