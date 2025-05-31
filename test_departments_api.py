#!/usr/bin/env python3
"""
🛏️ BED MAGIC API TESTER! 
Test the departments endpoint to make sure it works correctly
"""

import os
import django
import sys
import json

# Setup Django environment
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.views.hospital.hospital_views import departments
from api.models import CustomUser, Hospital
from django.test import RequestFactory
from rest_framework.test import force_authenticate
from django.contrib.auth import get_user_model

def test_departments_endpoint():
    """Test if the departments endpoint works correctly"""
    
    print("🛏️ Testing Department API Endpoint...")
    
    # Create a test request
    factory = RequestFactory()
    request = factory.get('/api/departments/')
    
    # Get a hospital admin user for testing
    try:
        hospital_admin = CustomUser.objects.filter(role='hospital_admin').first()
        if not hospital_admin:
            print("❌ No hospital admin found for testing")
            return
            
        print(f"🔑 Testing with user: {hospital_admin.email}")
        print(f"🏥 User's hospital: {hospital_admin.hospital.name if hospital_admin.hospital else 'None'}")
        
        # Authenticate the request
        force_authenticate(request, user=hospital_admin)
        
        # Call the departments view
        response = departments(request)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if hasattr(response, 'data'):
            print(f"📊 Response Data: {json.dumps(response.data, indent=2, default=str)}")
        else:
            print(f"📊 Response Content: {response.content}")
            
    except Exception as e:
        print(f"❌ Error testing endpoint: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_departments_endpoint()
