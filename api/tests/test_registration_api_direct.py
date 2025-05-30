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

# Import models directly to work with the database
from api.models import HospitalRegistration, CustomUser
from django.utils import timezone

# Base URL for API requests
BASE_URL = 'http://localhost:5000'

# Function to get pending registrations directly from the database
def get_pending_registrations_db(hospital_name):
    try:
        # Find all pending registrations for the specified hospital
        pending_registrations = HospitalRegistration.objects.filter(
            status='pending',
            hospital__name=hospital_name
        ).select_related('user', 'hospital')
        
        if not pending_registrations:
            print(f"No pending registrations found for {hospital_name}.")
            return []
        
        print(f"\nFound {pending_registrations.count()} pending registration(s) for {hospital_name}:")
        
        registrations_list = []
        for reg in pending_registrations:
            reg_data = {
                'id': reg.id,
                'user_name': f"{reg.user.first_name} {reg.user.last_name}",
                'user_email': reg.user.email,
                'hospital_name': reg.hospital.name,
                'created_at': reg.created_at
            }
            registrations_list.append(reg_data)
            
            print(f"\nID: {reg.id} - User: {reg.user.first_name} {reg.user.last_name} ({reg.user.email})")
            print(f"Hospital: {reg.hospital.name}")
            print(f"Registration date: {reg.created_at}")
            print("-" * 50)
            
        return registrations_list
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

# Function to approve registration directly in the database
def approve_registration_db(registration_id):
    try:
        # Find the registration
        registration = HospitalRegistration.objects.get(id=registration_id)
        
        # Display registration details before approval
        print(f"\nFound registration for {registration.user.first_name} {registration.user.last_name}")
        print(f"Hospital: {registration.hospital.name}")
        print(f"Status: {registration.status}")
        print(f"Registration date: {registration.created_at}")
        
        # Approve the registration
        registration.status = 'approved'
        registration.approved_date = timezone.now()
        registration.save()
        
        print(f"\nRegistration APPROVED successfully!")
        print(f"New status: {registration.status}")
        print(f"Approval date: {registration.approved_date}")
        
        # Check if this is the user's only approved registration
        other_approved = HospitalRegistration.objects.filter(
            user=registration.user,
            status='approved'
        ).exclude(id=registration.id).exists()
        
        # Set as primary if it's the only approved registration
        if not other_approved and not registration.is_primary:
            registration.is_primary = True
            registration.save()
            print("\nThis is now set as the user's primary hospital")
            
        return True
    
    except HospitalRegistration.DoesNotExist:
        print(f"No registration found with ID {registration_id}")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

# Main function
def main():
    # Get pending registrations for Abuja General Hospital
    hospital_name = "Abuja General Hospital"
    registrations = get_pending_registrations_db(hospital_name)
    
    if not registrations:
        print("No pending registrations to approve.")
        return
    
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
                success = approve_registration_db(reg_id)
                
                if success:
                    # Update the list of pending registrations
                    print("\nUpdating list of pending registrations...")
                    registrations = get_pending_registrations_db(hospital_name)
                    
                    if not registrations:
                        print("No more pending registrations.")
                        break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number or 'q' to quit.")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
