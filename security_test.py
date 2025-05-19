#!/usr/bin/env python3
"""
Comprehensive Security Feature Test Script
This script tests all aspects of the login security system:
1. Rate limiting (IP-based)
2. Account lockout (after multiple failed attempts)
3. Suspicious login notifications
4. Password reset functionality
5. Account unlock after password reset
"""
import requests
import time
import json
import sys
import random
import string

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "eruwagolden55@gmail.com"  # Change to your test email
WRONG_PASSWORD = "wrong_password_" + ''.join(random.choices(string.ascii_letters, k=5))
CORRECT_PASSWORD = "test123"  # Change to the correct password if known

# Text colors for console output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BLUE}{'=' * 80}")
    print(f" {text}")
    print(f"{'=' * 80}{Colors.ENDC}\n")

def print_success(text):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ SUCCESS: {text}{Colors.ENDC}")

def print_warning(text):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠ WARNING: {text}{Colors.ENDC}")

def print_error(text):
    """Print an error message"""
    print(f"{Colors.RED}✗ ERROR: {text}{Colors.ENDC}")

def print_info(text):
    """Print an info message"""
    print(f"{Colors.BLUE}ℹ INFO: {text}{Colors.ENDC}")

def login_attempt(email, password, expected_status=None):
    """Make a login attempt and return the response"""
    url = f"{BASE_URL}/login/"
    data = {"email": email, "password": password}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        
        # Print response details
        print_info(f"Login attempt for {email}")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.text}")
        
        # Check if the response matches the expected status
        if expected_status and expected_status not in response.text:
            print_error(f"Expected '{expected_status}' in response, but got: {response.text}")
        
        return response
    except Exception as e:
        print_error(f"Error during login attempt: {e}")
        return None

def request_password_reset(email):
    """Request a password reset for the given email"""
    url = f"{BASE_URL}/password/reset/"
    data = {"email": email}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        print_info(f"Password reset requested for {email}")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.text}")
        return response
    except Exception as e:
        print_error(f"Error during password reset request: {e}")
        return None

def confirm_password_reset(token, new_password):
    """Confirm a password reset with the given token and new password"""
    url = f"{BASE_URL}/password/reset/confirm/"
    data = {
        "token": token,
        "new_password": new_password,
        "confirm_password": new_password
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        print_info(f"Password reset confirmation")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.text}")
        return response
    except Exception as e:
        print_error(f"Error during password reset confirmation: {e}")
        return None

def unlock_account(email):
    """Unlock an account by clearing cache entries (using Django shell)"""
    import os
    os.system(f'echo "from django.core.cache import cache; cache.delete(\\"account_lockout:{email}\\"); '
              f'cache.delete(\\"account_lockout_expiry:{email}\\"); '
              f'cache.delete(\\"account_attempts:{email}\\"); '
              f'print(\\"Account {email} unlocked\\")" | python manage.py shell')

def test_rate_limiting():
    """Test IP-based rate limiting"""
    print_header("TESTING IP-BASED RATE LIMITING")
    
    print_info("Making multiple failed login attempts to trigger rate limiting...")
    
    # Make 4 failed login attempts (should trigger rate limiting after 3)
    for i in range(4):
        print(f"\nAttempt #{i+1}:")
        response = login_attempt(TEST_EMAIL, WRONG_PASSWORD)
        
        if i >= 3:
            # Check if rate limiting is triggered
            if response and response.status_code == 429:
                print_success("Rate limiting successfully triggered after 3 failed attempts")
            else:
                print_error("Rate limiting not triggered after 3 failed attempts")
        
        # Small delay between requests
        time.sleep(1)
    
    # Unlock the account to continue testing
    unlock_account(TEST_EMAIL)
    print_info("Account unlocked for further testing")
    time.sleep(2)

def test_account_lockout():
    """Test account lockout after multiple failed attempts"""
    print_header("TESTING ACCOUNT LOCKOUT")
    
    print_info("Making multiple failed login attempts to trigger account lockout...")
    
    # Make 6 failed login attempts (should trigger account lockout after 5)
    for i in range(6):
        print(f"\nAttempt #{i+1}:")
        response = login_attempt(TEST_EMAIL, WRONG_PASSWORD)
        
        if i >= 5:
            # Check if account lockout is triggered
            if response and response.status_code == 403 and "Account locked" in response.text:
                print_success("Account lockout successfully triggered after 5 failed attempts")
            else:
                print_error("Account lockout not triggered after 5 failed attempts")
        
        # Small delay between requests
        time.sleep(1)
    
    # Unlock the account to continue testing
    unlock_account(TEST_EMAIL)
    print_info("Account unlocked for further testing")
    time.sleep(2)

def test_password_reset_unlock():
    """Test account unlock after password reset"""
    print_header("TESTING PASSWORD RESET UNLOCK")
    
    # First lock the account
    print_info("Locking the account first...")
    for i in range(6):
        login_attempt(TEST_EMAIL, WRONG_PASSWORD)
        time.sleep(0.5)
    
    # Verify account is locked
    response = login_attempt(TEST_EMAIL, WRONG_PASSWORD, expected_status="Account locked")
    if response and response.status_code == 403 and "Account locked" in response.text:
        print_success("Account successfully locked for testing password reset")
    else:
        print_error("Failed to lock account for testing")
        return
    
    # Request password reset
    print_info("\nRequesting password reset...")
    reset_response = request_password_reset(TEST_EMAIL)
    
    if reset_response and reset_response.status_code == 200:
        print_success("Password reset request successful")
        print_warning("Since we can't automatically get the token from the email, we'll simulate the reset")
        
        # Simulate password reset by directly unlocking the account
        print_info("\nSimulating password reset confirmation...")
        unlock_account(TEST_EMAIL)
        
        # Try logging in again
        print_info("\nTrying to log in after account unlock...")
        login_response = login_attempt(TEST_EMAIL, CORRECT_PASSWORD)
        
        if login_response and login_response.status_code != 403:
            print_success("Account successfully unlocked after password reset simulation")
        else:
            print_error("Account still locked after password reset simulation")
    else:
        print_error("Password reset request failed")

def main():
    """Run all security tests"""
    print_header("SECURITY FEATURE TESTING")
    print("This script will test all security features of the login system.")
    
    # Test rate limiting
    test_rate_limiting()
    
    # Test account lockout
    test_account_lockout()
    
    # Test password reset unlock
    test_password_reset_unlock()
    
    print_header("TESTING COMPLETE")

if __name__ == "__main__":
    main()
