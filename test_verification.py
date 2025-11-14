#!/usr/bin/env python
"""
Test script for prescription verification endpoints.
This tests the public pharmacy verification API without authentication.
"""

import requests
import json

# Test data from prescription #7 (Amoxicillin)
TEST_QR_DATA = {
    "payload": {
        "type": "PHB_PRESCRIPTION",
        "id": "PHB-RX-00000007",
        "nonce": "9b9eee9e-906d-4e72-b566-bc9e50f6caa4",
        "hpn": "OGB 528 966 7838",
        "medication": "Amoxicillin",
        "strength": "500mg",
        "patient": "eruwa al-amin",
        "prescriber": "Unknown Prescriber",
        "dosage": "1 tablet",
        "frequency": "Three times daily",
        "pharmacy": {
            "name": "MedPlus Pharmacy Abuja",
            "code": "PHB-PH-003",
            "address": "78 Wuse II District",
            "city": "Abuja",
            "postcode": "900001",
            "phone": "+234-9-876-5432"
        },
        "issued": "2025-10-22T16:07:26.979676+00:00",
        "expiry": "2025-11-21T16:07:26.979676+00:00"
    },
    "signature": "cbec8b3bc04a43b74107fddac4477999dc23cbbcd6a7f6fe7c75e24ef38efa93"
}

BASE_URL = "http://localhost:8000"

def test_verify_prescription():
    """Test the verification endpoint"""
    print("=" * 60)
    print("Testing Prescription Verification Endpoint")
    print("=" * 60)

    url = f"{BASE_URL}/api/prescriptions/verify/"

    payload = {
        "payload": TEST_QR_DATA["payload"],
        "signature": TEST_QR_DATA["signature"],
        "pharmacy_code": "PHB-PH-003",
        "pharmacy_name": "MedPlus Pharmacy Abuja"
    }

    try:
        print(f"\nPOST {url}")
        print(f"Request data: {json.dumps(payload, indent=2)[:200]}...")

        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code == 200:
            result = response.json()
            if result.get('valid'):
                print("\n✅ SUCCESS: Prescription is VALID")
                return True
            else:
                print(f"\n⚠️  Prescription INVALID: {result.get('reason')}")
                return False
        else:
            print(f"\n❌ ERROR: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        return False


def test_dispense_prescription():
    """Test the dispensing endpoint"""
    print("\n" + "=" * 60)
    print("Testing Prescription Dispensing Endpoint")
    print("=" * 60)

    url = f"{BASE_URL}/api/prescriptions/dispense/"

    payload = {
        "prescription_id": TEST_QR_DATA["payload"]["id"],
        "nonce": TEST_QR_DATA["payload"]["nonce"],
        "pharmacy_code": "PHB-PH-003",
        "pharmacist_name": "John Smith",
        "verification_notes": "Patient ID verified"
    }

    try:
        print(f"\nPOST {url}")
        print(f"Request data: {json.dumps(payload, indent=2)}")

        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("\n✅ SUCCESS: Prescription DISPENSED")
                return True
            else:
                print(f"\n⚠️  Dispensing FAILED: {result.get('message')}")
                return False
        else:
            print(f"\n❌ ERROR: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n🏥 PHB Prescription Verification Test Suite\n")

    # Test 1: Verify prescription
    verify_success = test_verify_prescription()

    # Test 2: Dispense prescription (only if verification succeeded)
    if verify_success:
        input("\nPress Enter to test dispensing (this will mark the prescription as used)...")
        dispense_success = test_dispense_prescription()

        # Test 3: Try to verify again (should show "already dispensed")
        if dispense_success:
            input("\nPress Enter to verify again (should fail with 'already dispensed')...")
            test_verify_prescription()

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60 + "\n")
