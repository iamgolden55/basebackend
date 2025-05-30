# Script to test hospital admin APIs with correct login endpoint
import os
import django
import requests
import json
from pprint import pprint

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import Hospital, HospitalAdmin

# Base URL for API calls
BASE_URL = "http://localhost:8000/api"

def print_header(message):
    print("\n" + "="*80)
    print(f" {message} ".center(80, "="))
    print("="*80)

def print_response(response, limit=None):
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        if limit and isinstance(data, list) and len(data) > limit:
            print(f"Response (showing first {limit} items):")
            pprint(data[:limit])
            print(f"... and {len(data) - limit} more items")
        else:
            print("Response:")
            pprint(data)
    except ValueError:
        print("Response (not JSON):")
        print(response.text[:500] + "..." if len(response.text) > 500 else response.text)

def login_hospital_admin():
    print_header("LOGGING IN AS HOSPITAL ADMIN")
    
    # Get the Abuja hospital and admin
    hospital = Hospital.objects.filter(name="Abuja General Hospital").first()
    admin = HospitalAdmin.objects.filter(hospital=hospital).first()
    
    if not hospital or not admin:
        print("❌ Abuja General Hospital or its admin not found!")
        return None
    
    print(f"Found hospital: {hospital.name}")
    print(f"Found admin: {admin.email}")
    print(f"Hospital code: {hospital.registration_number}")
    
    # Try multiple possible login endpoints based on the dedicated hospital admin flow
    login_endpoints = [
        "/auth/hospital-admin/login/",
        "/login/hospital-admin/",
        "/token/hospital-admin/",
        "/auth/hospital/login/",
        "/token/"  # Standard token endpoint as fallback
    ]
    
    login_data = {
        "email": admin.email,
        "password": "AbujaAdmin2025",  # Default password from setup
        "hospital_code": hospital.registration_number
    }
    
    for endpoint in login_endpoints:
        login_url = f"{BASE_URL}{endpoint}"
        print(f"Trying login endpoint: {login_url}")
        
        try:
            response = requests.post(login_url, json=login_data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    token = data.get("access") or data.get("token")
                    if token:
                        print("✅ Login successful! Got access token.")
                        return {
                            "hospital_id": hospital.id,
                            "token": token,
                            "headers": {"Authorization": f"Bearer {token}"}
                        }
                    else:
                        print("❌ Login response didn't contain access token.")
                except ValueError:
                    print("❌ Response was not valid JSON.")
            else:
                print(f"❌ Login failed with status {response.status_code}")
        except Exception as e:
            print(f"❌ Error during login: {e}")
    
    print("❌ All login attempts failed.")
    return None

def test_hospital_profile_api(auth_data):
    print_header("TESTING HOSPITAL PROFILE API")
    
    # Try multiple possible endpoints
    endpoints = [
        f"/hospitals/{auth_data['hospital_id']}/",
        f"/hospital/{auth_data['hospital_id']}/",
        f"/hospital/profile/{auth_data['hospital_id']}/"
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"Trying endpoint: {url}")
        
        try:
            response = requests.get(url, headers=auth_data["headers"])
            print_response(response)
            
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

def test_dashboard_summary_api(auth_data):
    print_header("TESTING DASHBOARD SUMMARY API")
    
    # Try multiple possible endpoints
    endpoints = [
        f"/hospitals/{auth_data['hospital_id']}/dashboard/",
        f"/dashboard/hospital/{auth_data['hospital_id']}/",
        f"/dashboard/"
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"Trying endpoint: {url}")
        
        try:
            response = requests.get(url, headers=auth_data["headers"])
            print_response(response)
            
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

def test_departments_api(auth_data):
    print_header("TESTING DEPARTMENTS API")
    
    # Try multiple possible endpoints
    endpoints = [
        f"/hospitals/{auth_data['hospital_id']}/departments/",
        f"/departments/?hospital={auth_data['hospital_id']}",
        f"/hospital/{auth_data['hospital_id']}/departments/"
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"Trying endpoint: {url}")
        
        try:
            response = requests.get(url, headers=auth_data["headers"])
            print_response(response, limit=3)
            
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

def test_staff_on_duty_api(auth_data):
    print_header("TESTING STAFF ON DUTY API")
    
    # Try multiple possible endpoints
    endpoints = [
        f"/hospitals/{auth_data['hospital_id']}/staff/on-duty/",
        f"/staff/on-duty/?hospital={auth_data['hospital_id']}",
        f"/hospital/{auth_data['hospital_id']}/staff/"
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"Trying endpoint: {url}")
        
        try:
            response = requests.get(url, headers=auth_data["headers"])
            print_response(response, limit=5)
            
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

def test_appointments_api(auth_data):
    print_header("TESTING APPOINTMENTS API")
    
    # Try multiple possible endpoints
    endpoints = [
        f"/appointments/?hospital={auth_data['hospital_id']}",
        f"/hospitals/{auth_data['hospital_id']}/appointments/",
        f"/hospital/{auth_data['hospital_id']}/appointments/"
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"Trying endpoint: {url}")
        
        try:
            response = requests.get(url, headers=auth_data["headers"])
            print_response(response, limit=3)
            
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

def test_registrations_api(auth_data):
    print_header("TESTING REGISTRATIONS API")
    
    # Try multiple possible endpoints
    endpoints = [
        f"/hospitals/registrations/?status=pending&hospital={auth_data['hospital_id']}",
        f"/hospital/registrations/?status=pending&hospital={auth_data['hospital_id']}",
        f"/registrations/?status=pending&hospital={auth_data['hospital_id']}"
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"Trying endpoint: {url}")
        
        try:
            response = requests.get(url, headers=auth_data["headers"])
            print_response(response, limit=3)
            
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

def main():
    print_header("HOSPITAL ADMIN API TEST")
    
    # Login as hospital admin
    auth_data = login_hospital_admin()
    if not auth_data:
        print("❌ Failed to authenticate. Cannot proceed with API tests.")
        return
    
    # Test each API
    apis_to_test = [
        ("Hospital Profile", test_hospital_profile_api),
        ("Dashboard Summary", test_dashboard_summary_api),
        ("Departments List", test_departments_api),
        ("Staff on Duty", test_staff_on_duty_api),
        ("Appointments", test_appointments_api),
        ("Pending Registrations", test_registrations_api)
    ]
    
    results = []
    
    for api_name, test_func in apis_to_test:
        success = test_func(auth_data)
        results.append((api_name, success))
    
    # Print summary
    print_header("TEST RESULTS SUMMARY")
    for api_name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{api_name}: {status}")

if __name__ == "__main__":
    main()
