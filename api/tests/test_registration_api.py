import os
import django
import sys
import requests
import json

# Adjust the Python path to include the parent directory of 'api'
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# Base URL for API requests
BASE_URL = 'http://localhost:8000'

# Function to get an access token
def get_access_token(email, password, hospital_code):
    url = f"{BASE_URL}/api/hospitals/admin/login/"
    data = {
        'email': email,
        'password': password,
        'hospital_code': hospital_code
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f"Failed to get token: {response.text}")
        return None

# Function to get pending registrations
def get_pending_registrations(token):
    url = f"{BASE_URL}/api/hospitals/registrations/pending/"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get pending registrations: {response.text}")
        return None

# Function to approve a registration
def approve_registration(token, registration_id):
    url = f"{BASE_URL}/api/hospitals/registrations/{registration_id}/approve/"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to approve registration: {response.text}")
        return None

# Main function to run the tests
def main():
    # Get access token
    email = 'admin.stnicholas65@example.com'
    password = 'Password123!'
    hospital_code = 'H-C96166C1'
    
    print(f"Getting access token for {email}...")
    token = get_access_token(email, password, hospital_code)
    
    if not token:
        print("Failed to get access token. Exiting.")
        return
    
    print("Access token obtained successfully!")
    
    # Get pending registrations
    print("\nFetching pending registrations...")
    pending_data = get_pending_registrations(token)
    
    if not pending_data:
        print("No pending registrations data found. Exiting.")
        return
    
    # Check if we're looking at hospital admin view or system admin view
    if 'pending_registrations' in pending_data:
        # Hospital admin view
        registrations = pending_data['pending_registrations']
        total = pending_data['total_pending']
        print(f"Found {total} pending registration(s) for {pending_data.get('hospital_name', 'your hospital')}")
    elif 'hospitals_with_pending' in pending_data:
        # System admin view
        hospitals = pending_data['hospitals_with_pending']
        total_hospitals = pending_data['total_hospitals']
        total_registrations = pending_data['total_pending_registrations']
        print(f"Found {total_registrations} pending registration(s) across {total_hospitals} hospital(s)")
        
        # Flatten the registrations list
        registrations = []
        for hospital in hospitals:
            for reg in hospital['pending_registrations']:
                registrations.append(reg)
    else:
        print("Unexpected response format. Exiting.")
        return
    
    # Display pending registrations
    if not registrations:
        print("No pending registrations found.")
        return
    
    print("\nPending Registrations:")
    for i, reg in enumerate(registrations, 1):
        print(f"{i}. ID: {reg['id']} - User: {reg['user_name']} ({reg['user_email']})")
        print(f"   Hospital: {reg['hospital_name']}")
        print(f"   Registration date: {reg['created_at']}")
        print("   " + "-" * 50)
    
    # Ask if user wants to approve a registration
    while True:
        try:
            choice = input("\nEnter the number of the registration to approve (or 'q' to quit): ")
            
            if choice.lower() == 'q':
                break
            
            index = int(choice) - 1
            if 0 <= index < len(registrations):
                reg_id = registrations[index]['id']
                print(f"\nApproving registration ID {reg_id}...")
                result = approve_registration(token, reg_id)
                
                if result:
                    print("Registration approved successfully!")
                    print(f"New status: {result['registration']['status']}")
                    print(f"Approval date: {result['registration']['approved_date']}")
                    
                    # Update the list of pending registrations
                    print("\nUpdating list of pending registrations...")
                    pending_data = get_pending_registrations(token)
                    if pending_data:
                        print("Pending registrations updated.")
                        # Refresh the registrations list
                        if 'pending_registrations' in pending_data:
                            registrations = pending_data['pending_registrations']
                        elif 'hospitals_with_pending' in pending_data:
                            registrations = []
                            for hospital in pending_data['hospitals_with_pending']:
                                for reg in hospital['pending_registrations']:
                                    registrations.append(reg)
                        
                        if not registrations:
                            print("No more pending registrations.")
                            break
                        
                        print("\nRemaining Pending Registrations:")
                        for i, reg in enumerate(registrations, 1):
                            print(f"{i}. ID: {reg['id']} - User: {reg['user_name']} ({reg['user_email']})")
                            print(f"   Hospital: {reg['hospital_name']}")
                            print(f"   Registration date: {reg['created_at']}")
                            print("   " + "-" * 50)
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number or 'q' to quit.")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
