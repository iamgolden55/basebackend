#!/usr/bin/env python3
import os
import sys
import django
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# Now import Django models
from api.models import Hospital, Department

def list_hospitals():
    try:
        # Get all hospitals
        hospitals = Hospital.objects.all()
        
        # Create a list of hospital data
        data = []
        for hospital in hospitals:
            # Get departments in this hospital
            departments = Department.objects.filter(hospital=hospital)
            
            data.append({
                'id': hospital.id,
                'name': hospital.name,
                'address': hospital.address,
                'city': hospital.city,
                'state': hospital.state,
                'country': hospital.country,
                'departments': [
                    {
                        'id': dept.id,
                        'name': dept.name,
                        'code': dept.code
                    }
                    for dept in departments
                ]
            })
        
        return data
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # List hospitals
    hospitals = list_hospitals()
    
    # Print as JSON
    print(json.dumps(hospitals, indent=2)) 