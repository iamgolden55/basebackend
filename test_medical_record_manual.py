import requests
import os
import json
from pprint import pprint
import time

# Test configuration
BASE_URL = "http://127.0.0.1:8000/api"

def print_section(title):
    """Print a section title"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def get_token():
    """Login and get auth token"""
    print_section("Generating Auth Token")
    
    # Update these with valid credentials
    login_data = {
        "email": input("Enter test user email: "),
        "password": input("Enter test user password: ")
    }
    
    try:
        # Step 1: Initial login
        response = requests.post(f"{BASE_URL}/login/", json=login_data)
        if response.status_code != 200:
            print(f"Login failed with status code: {response.status_code}")
            try:
                print(response.json())
            except:
                print(response.text)
            return None
        
        response_data = response.json()
        print("Login successful!")
        
        # Check if OTP is required
        if response_data.get('require_otp'):
            print("OTP verification required")
            otp_code = input("Enter your OTP code: ")
            
            # Step 2: Verify OTP - using the correct URL
            otp_data = {
                "email": login_data["email"],
                "otp": otp_code
            }
            
            otp_response = requests.post(f"{BASE_URL}/verify-login-otp/", json=otp_data)
            if otp_response.status_code != 200:
                print(f"OTP verification failed with status code: {otp_response.status_code}")
                try:
                    print(otp_response.json())
                except:
                    print(otp_response.text)
                return None
                
            response_data = otp_response.json()
            print("OTP verification successful!")
        
        # Extract token from the final response, handling nested structure
        token = None
        if 'token' in response_data:
            token = response_data['token']
        elif 'access' in response_data:
            token = response_data['access']
        elif 'tokens' in response_data and 'access' in response_data['tokens']:
            token = response_data['tokens']['access']
            print("Found token in nested 'tokens.access' field")
        
        if token:
            print("Token obtained successfully")
            return token
        else:
            print("Could not find token in response")
            print(f"Response keys: {list(response_data.keys())}")
            print("Response content:")
            pprint(response_data)
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

def get_medical_record_access(auth_token):
    """Request and verify OTP for medical record access"""
    print_section("Getting Medical Record Access")
    
    if not auth_token:
        print("No auth token available.")
        return None
        
    headers = {
        "Authorization": f"Bearer {auth_token}"
    }
    
    # Step 1: Request Medical Record OTP
    print("\nRequesting Medical Record OTP...")
    try:
        response = requests.post(
            f"{BASE_URL}/patient/medical-record/request-otp/", 
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Failed to request medical record OTP. Status code: {response.status_code}")
            try:
                print(response.json())
            except:
                print(response.text)
            return None
            
        print("Medical Record OTP requested successfully")
        print("Check your email for the OTP code")
        
        # Step 2: Get OTP from user and verify
        med_otp = input("Enter the Medical Record OTP from your email: ")
        
        otp_data = {"otp": med_otp}
        verify_response = requests.post(
            f"{BASE_URL}/patient/medical-record/verify-otp/",
            json=otp_data,
            headers=headers
        )
        
        if verify_response.status_code != 200:
            print(f"Failed to verify medical record OTP. Status code: {verify_response.status_code}")
            try:
                print(verify_response.json())
            except:
                print(verify_response.text)
            return None
            
        verify_data = verify_response.json()
        med_access_token = verify_data.get('med_access_token')
        
        if not med_access_token:
            print("No medical record access token received")
            return None
            
        print("Medical Record access granted!")
        print(f"Access will expire in {verify_data.get('expires_in', 1800)//60} minutes")
        
        return med_access_token
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

def fetch_medical_record(auth_token, med_access_token):
    """Fetch the user's medical record with both tokens"""
    print_section("Fetching Medical Record")
    
    if not auth_token or not med_access_token:
        print("Missing required tokens.")
        return
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "X-Med-Access-Token": med_access_token
    }
    
    try:
        response = requests.get(f"{BASE_URL}/patient/medical-record/", headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            medical_record = response.json()
            print("Medical Record retrieved successfully:")
            pprint(medical_record)
        else:
            print("Failed to retrieve medical record")
            try:
                print(response.json())
            except:
                print(response.text)
    
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

def run_test():
    """Run the full test sequence"""
    print("Medical Record API Manual Test")
    print("-----------------------------")
    print("This script tests the security and functionality of the medical record API")
    print("Note: This implementation now requires DOUBLE OTP verification:")
    print("1. First OTP for general login")
    print("2. Second OTP specifically for medical record access")
    
    # Optionally configure server URL
    global BASE_URL
    user_url = input(f"Enter server URL (default: {BASE_URL}): ")
    if user_url.strip():
        BASE_URL = user_url
    
    # Step 1: Get authentication token
    auth_token = get_token()
    if not auth_token:
        print("Cannot proceed without authentication token.")
        return
        
    # Step 2: Get medical record access token through OTP verification
    med_access_token = get_medical_record_access(auth_token)
    if not med_access_token:
        print("Cannot proceed without medical record access token.")
        return
    
    # Step 3: Fetch medical record with both tokens
    fetch_medical_record(auth_token, med_access_token)

if __name__ == "__main__":
    run_test() 