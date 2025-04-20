from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.models.medical.doctor_assignment import doctor_assigner
from api.models.medical.hospital import Hospital
from api.models.medical.department import Department
from api.models.user.custom_user import CustomUser
from api.models.medical.appointment import Appointment
from api.models.medical_staff.doctor import Doctor

class Command(BaseCommand):
    help = 'Test appointment scenarios with the doctor assignment system'

    def print_doctor_info(self, doctor):
        return f"Dr. {doctor.user.get_full_name()} (Experience: {doctor.years_of_experience} years, Languages: {doctor.languages_spoken})"

    def handle(self, *args, **options):
        # Get our test data
        hospital = Hospital.objects.get(name="City General Hospital")
        department = Department.objects.get(name="Cardiology")
        patient = CustomUser.objects.get(username="patient1")
        
        # Print current state
        self.stdout.write("\nCurrent Setup:")
        self.stdout.write(f"Patient: {patient.get_full_name()} (Languages: {patient.languages})")
        self.stdout.write("\nAvailable Doctors:")
        for doctor in Doctor.objects.filter(is_active=True):
            self.stdout.write(f"- {self.print_doctor_info(doctor)}")
            appointments = Appointment.objects.filter(doctor=doctor, status='confirmed').count()
            self.stdout.write(f"  Current appointments: {appointments}")
        
        # Test different scenarios
        
        # Scenario 1: Regular appointment (should prefer Dr. Smith due to Spanish language)
        self.stdout.write("\nScenario 1: Regular Appointment (Spanish-speaking patient)")
        appointment_data = {
            'patient': patient,
            'hospital': hospital,
            'department': department,
            'appointment_type': 'consultation',
            'priority': 'normal',
            'appointment_date': timezone.now() + timedelta(days=1, hours=14)  # Tomorrow at 2 PM
        }
        
        assigned_doctor = doctor_assigner.assign_doctor(appointment_data)
        self.stdout.write(f"Assigned doctor: {self.print_doctor_info(assigned_doctor)}")
        
        # Scenario 2: Emergency appointment (should consider both doctors)
        self.stdout.write("\nScenario 2: Emergency Appointment")
        emergency_data = appointment_data.copy()
        emergency_data['appointment_type'] = 'emergency'
        emergency_data['priority'] = 'emergency'
        emergency_data['appointment_date'] = timezone.now() + timedelta(hours=1)
        
        assigned_doctor = doctor_assigner.assign_doctor(emergency_data)
        self.stdout.write(f"Emergency assigned doctor: {self.print_doctor_info(assigned_doctor)}")
        
        # Scenario 3: Appointment when Dr. Jones has high workload
        self.stdout.write("\nScenario 3: High Workload Scenario")
        workload_data = appointment_data.copy()
        workload_data['appointment_date'] = timezone.now() + timedelta(days=1, hours=11)  # During Dr. Jones's busy time
        
        assigned_doctor = doctor_assigner.assign_doctor(workload_data)
        self.stdout.write(f"Workload scenario assigned doctor: {self.print_doctor_info(assigned_doctor)}") 