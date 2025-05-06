import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models.medical.department import Department

def check_departments():
    """List all departments in the database"""
    departments = Department.objects.all()
    
    print(f"Found {departments.count()} departments:")
    for dept in departments:
        hospital_name = dept.hospital.name if dept.hospital else "No hospital"
        print(f"ID: {dept.id}, Name: {dept.name}, Hospital: {hospital_name}")
        
if __name__ == "__main__":
    check_departments() 