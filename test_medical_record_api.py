import requests
import json
import os
from colorama import Fore, Style, init
import time

# Initialize colorama
init()

# Set the base URL for API requests
BASE_URL = "http://127.0.0.1:8000/api"  # Use 127.0.0.1 instead of localhost

def print_response(response, title="Response"):
    """Print a formatted API response with status code and JSON data"""
    try:
        print(f"\n{Fore.CYAN}=== {title} ({response.status_code}) ==={Style.RESET_ALL}")
        if response.status_code == 204:  # No content
            print("No content")
            return
            
        json_data = response.json()
        print(json.dumps(json_data, indent=2))
    except Exception as e:
        print(f"{Fore.RED}Error parsing response: {str(e)}{Style.RESET_ALL}")
        print(response.text)

def wait_for_server(max_attempts=5):
    """Wait for the server to be available"""
    print(f"{Fore.YELLOW}Checking if server is available...{Style.RESET_ALL}")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/health-check/", timeout=2)
            if response.status_code == 200:
                print(f"{Fore.GREEN}Server is available!{Style.RESET_ALL}")
                return True
        except requests.exceptions.RequestException:
            print(f"{Fore.YELLOW}Waiting for server (attempt {attempt+1}/{max_attempts})...{Style.RESET_ALL}")
            time.sleep(2)
    
    print(f"{Fore.RED}Server not available after {max_attempts} attempts.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Make sure the Django server is running with: python manage.py runserver{Style.RESET_ALL}")
    return False

def main():
    """Test the medical record API flow"""
    
    # First check if the server is available
    if not wait_for_server():
        return
    
    # Login credentials - Update with a valid user account
    login_data = {
        "email": "patient@example.com",  # Update with a real user
        "password": "SecureP@ssw0rd"     # Update with their password
    }
    
    print(f"\n{Fore.GREEN}Step 1: Login to obtain JWT token{Style.RESET_ALL}")
    try:
        login_response = requests.post(f"{BASE_URL}/login/", json=login_data)
        print_response(login_response, "Login Response")
        
        if login_response.status_code != 200:
            print(f"{Fore.RED}Login failed. Cannot continue tests.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Make sure you've provided valid login credentials and the login endpoint is working.{Style.RESET_ALL}")
            return
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Request error during login: {str(e)}{Style.RESET_ALL}")
        return
    
    try:
        # Extract token from response - handle different response structures
        response_data = login_response.json()
        print(f"{Fore.YELLOW}Response structure: {list(response_data.keys())}{Style.RESET_ALL}")
        
        access_token = None
        if 'tokens' in response_data:
            access_token = response_data.get('tokens', {}).get('access', '')
        elif 'access' in response_data:
            access_token = response_data.get('access', '')
        elif 'token' in response_data:
            access_token = response_data.get('token', '')
            
        if not access_token:
            print(f"{Fore.RED}Could not extract access token from response.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Response structure: {list(response_data.keys())}{Style.RESET_ALL}")
            return
            
        # Set authorization header with the token
        auth_header = {'Authorization': f'Bearer {access_token}'}
        
        # Test 1: Access medical record with valid authentication
        print(f"\n{Fore.GREEN}Step 2: Access medical record with valid token{Style.RESET_ALL}")
        try:
            med_record_response = requests.get(
                f"{BASE_URL}/patient/medical-record/", 
                headers=auth_header,
                timeout=5
            )
            print_response(med_record_response, "Medical Record Response")
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}Request error accessing medical record: {str(e)}{Style.RESET_ALL}")
        
        # Test 2: Try accessing without authentication
        print(f"\n{Fore.GREEN}Step 3: Try accessing without authentication (should fail){Style.RESET_ALL}")
        try:
            unauth_response = requests.get(f"{BASE_URL}/patient/medical-record/", timeout=5)
            print_response(unauth_response, "Unauthenticated Access Attempt")
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}Request error during unauthenticated access: {str(e)}{Style.RESET_ALL}")
        
        # Test 3: Try with invalid token
        print(f"\n{Fore.GREEN}Step 4: Try with invalid token (should fail){Style.RESET_ALL}")
        try:
            invalid_auth = {'Authorization': 'Bearer invalid_token_here'}
            invalid_token_response = requests.get(
                f"{BASE_URL}/patient/medical-record/", 
                headers=invalid_auth,
                timeout=5
            )
            print_response(invalid_token_response, "Invalid Token Attempt")
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}Request error during invalid token test: {str(e)}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}All tests completed!{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}Error during tests: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 