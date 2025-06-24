#!/usr/bin/env python3
"""
Test Paystack Integration on Heroku
"""
import requests
import json

HEROKU_URL = "https://basebackend-88c8c04dd3ab.herokuapp.com"

def test_paystack_config():
    print("💳 Testing Paystack Integration")
    print("=" * 40)
    
    # Test if payment endpoints exist
    endpoints = [
        "/api/payments/",
        "/api/health/",
        "/api/appointments/",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{HEROKU_URL}{endpoint}", timeout=10)
            print(f"📡 {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"📡 {endpoint}: ERROR - {str(e)}")

if __name__ == "__main__":
    test_paystack_config()
