#!/usr/bin/env python3
import requests
import json
import time
from colorama import Fore, Style, init

# Initialize colorama
init()

# Set the base URL
BASE_URL = "http://localhost:8001/api"

def print_response(response, title=None):
    """Pretty print a response"""
    if title:
        print(f"\n{Fore.BLUE}{title}{Style.RESET_ALL}")
    
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(f"Status code: {response.status_code}")
        print(response.text)
    
    print(f"Status code: {response.status_code}")

def check_success(response, expected_status=200):
    """Check if a response was successful"""
    return response.status_code == expected_status

def main():
    print(f"{Fore.BLUE}Starting Hospital Admin API Test Script{Style.RESET_ALL}")
    print("==============================================")
    
    # Scenario 1: Register a regular user first - needed for the admin registration
    print(f"\n{Fore.BLUE}Scenario 1: Register a regular user that will become an admin{Style.RESET_ALL}")
    user_data = {
        "email": "dr.emeka@example.com",
        "full_name": "Emeka Okonkwo",
        "password": "secure123password",
        "date_of_birth": "1975-08-15",
        "gender": "male",
        "phone": "+2347012345678",
        "country": "Nigeria",
        "state": "Lagos",
        "city": "Ikeja",
        "preferred_language": "en",
        "secondary_languages": ["yo", "ig"],
        "nin": "12345678901",  # Added NIN for Nigerian users
        "consent_terms": True,
        "consent_hipaa": True,
        "consent_data_processing": True
    }
    
    user_response = requests.post(f"{BASE_URL}/registration/", json=user_data)
    print_response(user_response, "User registration response:")
    
    # Scenario 2: Create a new hospital for testing
    print(f"\n{Fore.BLUE}Scenario 2: Creating a test hospital{Style.RESET_ALL}")
    hospital_data = {
        "name": "Test General Hospital",
        "address": "123 Test Street",
        "city": "Lagos",
        "state": "Lagos",
        "country": "Nigeria",
        "postal_code": "10001",
        "registration_number": "TGH123456",
        "hospital_type": "public",
        "emergency_unit": True,
        "icu_unit": True,
        "email": "info@testgeneralhospital.com",
        "phone": "+2347000000000"
    }
    
    # Try to get an authenticated user for hospital creation
    # Since we're just testing, we can create a temporary admin user
    temp_admin_data = {
        "email": "temp.admin@example.com",
        "full_name": "Temporary Admin",
        "password": "temp123admin",
        "date_of_birth": "1980-01-01",
        "gender": "male",
        "phone": "+2347099999999",
        "country": "Nigeria",
        "state": "Lagos",
        "city": "Lagos",
        "preferred_language": "en",
        "secondary_languages": ["en"],
        "nin": "11122233344",  # Added NIN for Nigerian users
        "consent_terms": True,
        "consent_hipaa": True,
        "consent_data_processing": True
    }
    
    # Register temp admin
    temp_admin_response = requests.post(f"{BASE_URL}/registration/", json=temp_admin_data)
    print_response(temp_admin_response, "Temporary admin registration response:")
    
    # Login as temp admin
    temp_login_data = {
        "email": "temp.admin@example.com",
        "password": "temp123admin"
    }
    
    temp_login_response = requests.post(f"{BASE_URL}/token/", json=temp_login_data)
    if not check_success(temp_login_response):
        temp_login_response = requests.post(f"{BASE_URL}/login/", json=temp_login_data)
    
    temp_token = ""
    if check_success(temp_login_response):
        if 'tokens' in temp_login_response.json():
            temp_token = temp_login_response.json().get('tokens', {}).get('access', '')
        elif 'access' in temp_login_response.json():
            temp_token = temp_login_response.json().get('access', '')
    
    # Now try to create hospital with token
    headers = {"Authorization": f"Bearer {temp_token}"} if temp_token else {}
    
    hospital_response = requests.post(
        f"{BASE_URL}/hospitals/register/",
        headers=headers,
        json=hospital_data
    )
    
    print_response(hospital_response, "Hospital creation response:")
    
    if not check_success(hospital_response, 201):
        print(f"{Fore.RED}Hospital creation failed, trying alternative approach...{Style.RESET_ALL}")
        # Try without authentication as a fallback
        hospital_response = requests.post(
            f"{BASE_URL}/hospitals/register/",
            json=hospital_data
        )
        print_response(hospital_response, "Hospital creation response (no auth):")
    
    if not check_success(hospital_response, 201):
        print(f"{Fore.RED}Hospital creation failed, but continuing with default ID...{Style.RESET_ALL}")
        hospital_id = 1  # Fallback to ID 1
    else:
        hospital_id = hospital_response.json().get('id', 1)
    
    print(f"Created hospital with ID: {hospital_id}")
    
    # Scenario 3: Convert existing user to hospital admin
    print(f"\n{Fore.BLUE}Scenario 3: Convert existing user to hospital admin{Style.RESET_ALL}")
    convert_data = {
        "existing_user": True,
        "user_email": "dr.emeka@example.com",
        "hospital": hospital_id,
        "position": "Medical Director"
    }
    
    convert_response = requests.post(
        f"{BASE_URL}/hospitals/admin/register/",
        json=convert_data
    )
    
    print_response(convert_response, "Convert user to admin response:")
    
    # Check if the user exists and is an admin
    print(f"\n{Fore.BLUE}Checking if dr.emeka@example.com exists and is an admin{Style.RESET_ALL}")
    user_check = requests.get(f"{BASE_URL}/hospitals/admin/check-user/?email=dr.emeka@example.com")
    print_response(user_check)
    
    # Scenario 4: Try to login with the new admin account
    print(f"\n{Fore.BLUE}Scenario 4: Login with the new admin account{Style.RESET_ALL}")
    login_data = {
        "email": "dr.emeka@example.com",
        "password": "secure123password"
    }
    
    # Try both login endpoints
    login_response = requests.post(f"{BASE_URL}/token/", json=login_data)
    if not check_success(login_response):
        print(f"{Fore.YELLOW}Token endpoint failed, trying login endpoint...{Style.RESET_ALL}")
        login_response = requests.post(f"{BASE_URL}/login/", json=login_data)
    
    print_response(login_response, "Login response:")
    
    if not check_success(login_response):
        print(f"{Fore.RED}Login failed, but continuing...{Style.RESET_ALL}")
        access_token = ""
    else:
        # Handle different response formats
        if 'tokens' in login_response.json():
            access_token = login_response.json().get('tokens', {}).get('access', '')
        elif 'access' in login_response.json():
            access_token = login_response.json().get('access', '')
        else:
            access_token = ""
        print(f"Access token obtained: {access_token[:20]}... (truncated)")
    
    # Scenario 5: Create a second user that will be converted to an admin
    print(f"\n{Fore.BLUE}Scenario 5: Register a second user{Style.RESET_ALL}")
    user2_data = {
        "email": "dr.ngozi@example.com",
        "full_name": "Ngozi Adeyemi",
        "password": "secure456password",
        "date_of_birth": "1980-03-22",
        "gender": "female",
        "phone": "+2348034567890",
        "country": "Nigeria",
        "state": "Abuja",
        "city": "Central District",
        "preferred_language": "en",
        "secondary_languages": ["ha"],
        "nin": "98765432109",  # Added NIN for Nigerian users
        "consent_terms": True,
        "consent_hipaa": True,
        "consent_data_processing": True
    }
    
    user2_response = requests.post(f"{BASE_URL}/registration/", json=user2_data)
    print_response(user2_response, "Second user registration response:")
    
    # Check if the second user exists but is not an admin
    print(f"\n{Fore.BLUE}Checking if dr.ngozi@example.com exists but is not an admin{Style.RESET_ALL}")
    user_check2 = requests.get(f"{BASE_URL}/hospitals/admin/check-user/?email=dr.ngozi@example.com")
    print_response(user_check2)
    
    # Scenario 6: Create a second hospital
    print(f"\n{Fore.BLUE}Scenario 6: Creating a second test hospital{Style.RESET_ALL}")
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    
    hospital2_data = {
        "name": "Sunshine Medical Center",
        "address": "456 Health Avenue",
        "city": "Abuja",
        "state": "FCT",
        "country": "Nigeria",
        "postal_code": "90001",
        "registration_number": "SMC789012",
        "hospital_type": "private",
        "emergency_unit": True,
        "icu_unit": True,
        "email": "info@sunshinemedical.com",
        "phone": "+2348000000000"
    }
    
    hospital2_response = requests.post(
        f"{BASE_URL}/hospitals/register/",
        headers=headers,
        json=hospital2_data
    )
    
    print_response(hospital2_response, "Second hospital creation response:")
    
    if not check_success(hospital2_response, 201):
        print(f"{Fore.RED}Second hospital creation failed, trying without auth...{Style.RESET_ALL}")
        hospital2_response = requests.post(
            f"{BASE_URL}/hospitals/register/",
            json=hospital2_data
        )
        print_response(hospital2_response, "Second hospital creation response (no auth):")
    
    if not check_success(hospital2_response, 201):
        print(f"{Fore.RED}Second hospital creation failed, but continuing...{Style.RESET_ALL}")
        hospital2_id = 2  # Fallback to ID 2
    else:
        hospital2_id = hospital2_response.json().get('id', 2)
    
    print(f"Created second hospital with ID: {hospital2_id}")
    
    # Scenario 7: Convert second user to hospital admin
    print(f"\n{Fore.BLUE}Scenario 7: Convert second user to hospital admin{Style.RESET_ALL}")
    convert2_data = {
        "existing_user": True,
        "user_email": "dr.ngozi@example.com",
        "hospital": hospital2_id,
        "position": "Chief Medical Officer"
    }
    
    convert2_response = requests.post(
        f"{BASE_URL}/hospitals/admin/register/",
        json=convert2_data
    )
    
    print_response(convert2_response, "Convert second user to admin response:")
    
    # Check if second user is now an admin
    print(f"\n{Fore.BLUE}Checking if dr.ngozi@example.com is now an admin{Style.RESET_ALL}")
    user_check3 = requests.get(f"{BASE_URL}/hospitals/admin/check-user/?email=dr.ngozi@example.com")
    print_response(user_check3)
    
    # Login with the second admin account
    print(f"\n{Fore.BLUE}Login with the second admin account{Style.RESET_ALL}")
    login2_data = {
        "email": "dr.ngozi@example.com",
        "password": "secure456password"
    }
    
    # Try both login endpoints
    login2_response = requests.post(f"{BASE_URL}/token/", json=login2_data)
    if not check_success(login2_response):
        print(f"{Fore.YELLOW}Token endpoint failed, trying login endpoint...{Style.RESET_ALL}")
        login2_response = requests.post(f"{BASE_URL}/login/", json=login2_data)
    
    print_response(login2_response, "Second admin login response:")
    
    if not check_success(login2_response):
        print(f"{Fore.RED}Second login failed, but continuing...{Style.RESET_ALL}")
        access_token2 = ""
    else:
        # Handle different response formats
        if 'tokens' in login2_response.json():
            access_token2 = login2_response.json().get('tokens', {}).get('access', '')
        elif 'access' in login2_response.json():
            access_token2 = login2_response.json().get('access', '')
        else:
            access_token2 = ""
        print(f"Second access token obtained: {access_token2[:20]}... (truncated)")
    
    # Scenario 8: Try to register an existing admin as admin again (should fail)
    print(f"\n{Fore.BLUE}Scenario 8: Try to register an existing admin as admin again (should fail){Style.RESET_ALL}")
    double_admin_data = {
        "existing_user": True,
        "user_email": "dr.emeka@example.com",
        "hospital": hospital2_id,
        "position": "Consultant"
    }
    
    double_admin_response = requests.post(
        f"{BASE_URL}/hospitals/admin/register/",
        json=double_admin_data
    )
    
    print_response(double_admin_response, "Double admin registration response (should fail):")
    
    # Scenario 9: Test invalid data submission
    print(f"\n{Fore.BLUE}Scenario 9: Test invalid data submission{Style.RESET_ALL}")
    invalid_data = {
        "email": "new.admin@example.com",
        "full_name": "New Admin",
        "password": "password123",
        "hospital": hospital_id
    }
    
    invalid_response = requests.post(
        f"{BASE_URL}/hospitals/admin/register/",
        json=invalid_data
    )
    
    print_response(invalid_response, "Invalid data submission response (should fail):")
    
    # Scenario 10: Get user registered hospitals (correct endpoint for staff registration)
    print(f"\n{Fore.BLUE}Scenario 10: Get user registered hospitals{Style.RESET_ALL}")
    headers2 = {"Authorization": f"Bearer {access_token2}"} if access_token2 else {}
    
    # Try different endpoints to find the correct one for hospital registration
    registration_endpoints = [
        "hospitals/registrations/",
        "hospitals/registration/",
        "hospitals/{hospital_id}/registration/",
        "hospitals/{hospital_id}/register/",
        "hospitals/user-registrations/"
    ]
    
    for endpoint in registration_endpoints:
        endpoint_url = endpoint.format(hospital_id=hospital_id)
        print(f"{Fore.YELLOW}Trying endpoint: {endpoint_url}{Style.RESET_ALL}")
        
        # Try GET first
        reg_response = requests.get(
            f"{BASE_URL}/{endpoint_url}",
            headers=headers2
        )
        
        if check_success(reg_response):
            print_response(reg_response, f"GET {endpoint_url} response (success):")
            break
        
        # Try POST if GET doesn't work
        reg_data = {
            "hospital": hospital_id,
            "is_primary": True
        }
        
        reg_response = requests.post(
            f"{BASE_URL}/{endpoint_url}",
            headers=headers2,
            json=reg_data
        )
        
        if check_success(reg_response, 201):
            print_response(reg_response, f"POST {endpoint_url} response (success):")
            break
        
        print(f"{Fore.RED}Endpoint {endpoint_url} failed with status: {reg_response.status_code}{Style.RESET_ALL}")
    
    # Scenario 11: View hospital staff registrations as admin
    print(f"\n{Fore.BLUE}Scenario 11: View hospital staff registrations as admin{Style.RESET_ALL}")
    registrations_response = requests.get(
        f"{BASE_URL}/hospitals/registrations/",
        headers=headers2  # Using the second admin token
    )
    
    print_response(registrations_response, "Hospital registrations view response:")
    
    if not check_success(registrations_response):
        print(f"{Fore.RED}Viewing registrations failed, but continuing...{Style.RESET_ALL}")
        registration_id = 1  # Fallback
    else:
        try:
            # Try to extract the first registration ID
            registrations = registrations_response.json()
            if isinstance(registrations, list) and len(registrations) > 0:
                registration_id = registrations[0].get('id', 1)
            else:
                registration_id = 1
                print(f"{Fore.YELLOW}No registrations found, using default ID 1{Style.RESET_ALL}")
        except:
            registration_id = 1
            print(f"{Fore.RED}Error parsing registrations, using default ID 1{Style.RESET_ALL}")
    
    # Scenario 12: Approve staff registration
    print(f"\n{Fore.BLUE}Scenario 12: Approve staff registration with ID {registration_id}{Style.RESET_ALL}")
    approve_response = requests.post(
        f"{BASE_URL}/hospitals/registrations/{registration_id}/approve/",
        headers=headers2  # Using the second admin token
    )
    
    print_response(approve_response, "Registration approval response:")
    
    print(f"\n{Fore.GREEN}All test scenarios completed!{Style.RESET_ALL}")
    print("==============================================")

if __name__ == "__main__":
    main() 