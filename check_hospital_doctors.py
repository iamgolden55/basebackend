import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical_staff.doctor import Doctor
from api.models.medical.department import Department
from api.models.medical.hospital import Hospital

def check_doctors():
    """List all doctors in the database with their departments and availability"""
    doctors = Doctor.objects.all()
    
    print(f"Found {doctors.count()} doctors:")
    for doctor in doctors:
        hospital_name = doctor.hospital.name if doctor.hospital else "No hospital"
        department_name = doctor.department.name if doctor.department else "No department"
        
        print(f"\nID: {doctor.id}, Name: {doctor.full_name}")
        print(f"Hospital: {hospital_name}")
        print(f"Department: {department_name}")
        print(f"Specialization: {doctor.specialization}")
        print(f"Available for appointments: {doctor.available_for_appointments}")
        
        if doctor.consultation_hours_start and doctor.consultation_hours_end:
            print(f"Consultation hours: {doctor.consultation_hours_start} - {doctor.consultation_hours_end}")
        
        if doctor.consultation_days:
            print(f"Consultation days: {doctor.consultation_days}")
        
        print(f"Max daily appointments: {doctor.max_daily_appointments}")
        print(f"Appointment duration: {doctor.appointment_duration} minutes")
        
def check_doctors_by_department():
    """List all departments and count doctors in each"""
    departments = Department.objects.all()
    
    print("\nDoctors by Department:")
    for dept in departments:
        doctor_count = Doctor.objects.filter(department=dept, available_for_appointments=True).count()
        print(f"Department: {dept.name}, Hospital: {dept.hospital.name if dept.hospital else 'No hospital'}, Available Doctors: {doctor_count}")
        
        # Print doctors in this department
        doctors = Doctor.objects.filter(department=dept, available_for_appointments=True)
        for doctor in doctors:
            print(f"  - ID: {doctor.id}, Name: {doctor.full_name}")
        
if __name__ == "__main__":
    print("=" * 50)
    print("DOCTOR INFORMATION")
    print("=" * 50)
    check_doctors()
    
    print("\n" + "=" * 50)
    print("DEPARTMENT SUMMARY")
    print("=" * 50)
    check_doctors_by_department() 