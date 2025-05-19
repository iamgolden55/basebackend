#!/usr/bin/env python3
"""
Security Features Test Script
This script provides simple commands to test each security feature individually.
"""
import requests
import json
import os
import sys

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "eruwagolden55@gmail.com"

def login_attempt(email, password):
    """Make a login attempt and return the response"""
    url = f"{BASE_URL}/login/"
    data = {"email": email, "password": password}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response
    except Exception as e:
        print(f"Error during login attempt: {e}")
        return None

def request_password_reset(email):
    """Request a password reset for the given email"""
    url = f"{BASE_URL}/password/reset/"
    data = {"email": email}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response
    except Exception as e:
        print(f"Error during password reset request: {e}")
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
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response
    except Exception as e:
        print(f"Error during password reset confirmation: {e}")
        return None

def unlock_account(email):
    """Unlock an account by clearing cache entries (using Django shell)"""
    cmd = (f'echo "from django.core.cache import cache; '
           f'cache.delete(\\"account_lockout:{email}\\"); '
           f'cache.delete(\\"account_lockout_expiry:{email}\\"); '
           f'cache.delete(\\"account_attempts:{email}\\"); '
           f'cache.delete(\\"login_attempts:{email}\\"); '
           f'print(\\"Account {email} unlocked\\")" | python manage.py shell')
    os.system(cmd)

def print_help():
    """Print help information"""
    print("\nSecurity Features Test Script")
    print("============================")
    print("Commands:")
    print("  1. Test login with correct password")
    print("  2. Test login with incorrect password")
    print("  3. Request password reset")
    print("  4. Unlock account (clear lockout)")
    print("  5. Exit")
    print()

def main():
    """Main function to handle user input"""
    while True:
        print_help()
        choice = input("Enter your choice (1-5): ")
        
        if choice == "1":
            password = input("Enter correct password: ")
            print("\nTesting login with correct password...")
            login_attempt(TEST_EMAIL, password)
        
        elif choice == "2":
            password = input("Enter incorrect password: ")
            print("\nTesting login with incorrect password...")
            login_attempt(TEST_EMAIL, password)
        
        elif choice == "3":
            print("\nRequesting password reset...")
            request_password_reset(TEST_EMAIL)
            
            # Ask if user wants to simulate password reset confirmation
            simulate = input("\nDo you want to simulate password reset confirmation? (y/n): ")
            if simulate.lower() == 'y':
                token = input("Enter token (or 'skip' to skip): ")
                if token.lower() != 'skip':
                    new_password = input("Enter new password: ")
                    confirm_password_reset(token, new_password)
        
        elif choice == "4":
            print("\nUnlocking account...")
            unlock_account(TEST_EMAIL)
        
        elif choice == "5":
            print("\nExiting...")
            break
        
        else:
            print("\nInvalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
