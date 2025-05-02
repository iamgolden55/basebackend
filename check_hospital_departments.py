import os
import django
import sys
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital, Department

hospital_name = "Abuja Central Hospital"

try:
    # Get the hospital
    hospital = Hospital.objects.get(name=hospital_name)
    
    # Get all departments for this hospital
    departments = Department.objects.filter(hospital=hospital).order_by('name')
    
    # Count total departments
    total_departments = departments.count()
    
    print(f"\nDepartments at {hospital_name}:")
    print(f"Total departments: {total_departments}")
    
    if total_departments > 0:
        print("\nDepartment List:")
        print("-" * 50)
        
        for dept in departments:
            print(f"Name: {dept.name}")
            if hasattr(dept, 'description') and dept.description:
                print(f"Description: {dept.description}")
            if hasattr(dept, 'head_of_department') and dept.head_of_department:
                print(f"Head of Department: {dept.head_of_department}")
            print("-" * 50)
    else:
        print("\nNo departments found.")

except Hospital.DoesNotExist:
    print(f"Hospital '{hospital_name}' not found")
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1) 