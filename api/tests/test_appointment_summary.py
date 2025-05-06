import requests
import json
import os
from datetime import datetime

# Function to get an access token 
def get_access_token():
    """Get JWT access token by authenticating with a user"""
    response = requests.post('http://localhost:8000/api/auth/login/',
                            json={
                                'email': 'laminu_maina@icloud.com',
                                'password': 'TestPassword123!'  # Using a more likely password format
                            })
    if response.status_code == 200:
        data = response.json()
        print("Authentication successful!")
        return data.get('tokens', {}).get('access')
    else:
        print(f"Authentication failed: {response.text}")
        print("Let's try the token endpoint directly...")
        
        # Try another endpoint as fallback
        response = requests.post('http://localhost:8000/api/token/',
                                json={
                                    'email': 'laminu_maina@icloud.com',
                                    'password': 'TestPassword123!'
                                })
        if response.status_code == 200:
            print("Token endpoint authentication successful!")
            return response.json().get('access')
        else:
            print(f"Token endpoint authentication failed: {response.text}")
            
            # Try yet another common pattern
            response = requests.post('http://localhost:8000/api/auth/token/',
                                   json={
                                       'email': 'laminu_maina@icloud.com',
                                       'password': 'TestPassword123!'
                                   })
            if response.status_code == 200:
                print("Auth token endpoint authentication successful!")
                return response.json().get('access')
            
            return None

# Function to get appointment details
def get_appointment_summary(token, appointment_id):
    """Get appointment summary using the new API endpoint"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.get(f'http://localhost:8000/api/appointments/{appointment_id}/summary/',
                          headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get appointment summary: {response.status_code} - {response.text}")
        return None

# Function to get all appointments
def get_all_appointments(token):
    """Get all appointments for the authenticated user"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.get('http://localhost:8000/api/appointments/',
                          headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get appointments: {response.status_code} - {response.text}")
        return None

def print_appointment_summary(summary):
    """Print the appointment summary in a nicely formatted way"""
    if not summary:
        print("No summary data available")
        return
    
    details = summary.get('appointment_details', {})
    patient = summary.get('patient_details', {})
    notes = summary.get('important_notes', [])
    payment = summary.get('payment_info', {})
    
    print("\n" + "="*80)
    print(f"APPOINTMENT SUMMARY: {details.get('appointment_id')}")
    print("="*80 + "\n")
    
    print(f"📆 DATE & TIME: {details.get('formatted_date_time')}")
    print(f"👨‍⚕️ DOCTOR: {details.get('doctor')}")
    print(f"🏥 HOSPITAL: {details.get('hospital')}")
    print(f"🏢 DEPARTMENT: {details.get('department')}")
    print(f"⏱️ DURATION: {details.get('duration')}")
    print(f"📋 TYPE: {details.get('type')}")
    print(f"🚦 PRIORITY: {details.get('priority')}")
    print(f"🚥 STATUS: {details.get('status')}")
    
    print("\n👤 PATIENT INFORMATION:")
    print(f"  • Name: {patient.get('name')}")
    print(f"  • Chief Complaint: {patient.get('chief_complaint')}")
    
    if patient.get('symptoms'):
        print(f"  • Symptoms: {patient.get('symptoms')}")
    
    print("\n⚠️ IMPORTANT NOTES:")
    for i, note in enumerate(notes, 1):
        print(f"  {i}. {note}")
    
    print("\n💳 PAYMENT INFORMATION:")
    print(f"  • Payment Required: {'Yes' if payment.get('payment_required') else 'No'}")
    print(f"  • Payment Status: {payment.get('payment_status', 'N/A')}")
    print(f"  • Insurance-based: {'Yes' if payment.get('is_insurance_based') else 'No'}")
    
    print("\n" + "="*80)

def main():
    # Get authentication token
    token = get_access_token()
    if not token:
        print("Could not authenticate. Exiting.")
        return
    
    # Get all appointments
    appointments = get_all_appointments(token)
    if not appointments:
        print("No appointments found. Exiting.")
        return
    
    # Print appointment IDs for selection
    print("\nAvailable Appointments:")
    for i, appt in enumerate(appointments, 1):
        date = appt.get('formatted_date_time', appt.get('appointment_date', 'Unknown date'))
        doctor = appt.get('doctor_full_name', 'Unknown doctor')
        department = appt.get('department_name', 'Unknown department')
        print(f"{i}. ID: {appt.get('id')} - {date} with {doctor} ({department})")
    
    # Let user select an appointment
    try:
        selection = int(input("\nEnter the number of the appointment to view (or 0 to exit): "))
        if selection == 0:
            print("Exiting.")
            return
        
        if 1 <= selection <= len(appointments):
            selected_appointment = appointments[selection-1]
            appointment_id = selected_appointment.get('id')
            
            # Get and print summary
            summary = get_appointment_summary(token, appointment_id)
            print_appointment_summary(summary)
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a valid number.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 