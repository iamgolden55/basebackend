#!/bin/bash

# Set the base URL
BASE_URL="http://localhost:8000/api"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Hospital Admin API Test Script${NC}"
echo "=============================================="

# Scenario 1: Create a new hospital for testing
echo -e "\n${BLUE}Scenario 1: Creating a test hospital${NC}"
HOSPITAL_RESPONSE=$(curl -s -X POST "$BASE_URL/hospitals/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test General Hospital",
    "address": "123 Test Street",
    "city": "Lagos",
    "state": "Lagos",
    "country": "Nigeria",
    "postal_code": "10001",
    "registration_number": "TGH123456",
    "hospital_type": "public",
    "emergency_unit": true,
    "icu_unit": true,
    "email": "info@testgeneralhospital.com",
    "phone": "+2347000000000"
  }')

# Extract hospital ID
HOSPITAL_ID=$(echo $HOSPITAL_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d":" -f2)
echo "Created hospital with ID: $HOSPITAL_ID"

# Scenario 2: Register new user as hospital admin
echo -e "\n${BLUE}Scenario 2: Register new user as hospital admin${NC}"
curl -s -X POST "$BASE_URL/hospitals/admin/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dr.emeka@example.com",
    "full_name": "Emeka Okonkwo",
    "password": "secure123password",
    "hospital": '$HOSPITAL_ID',
    "position": "Medical Director",
    "date_of_birth": "1975-08-15",
    "gender": "male",
    "phone": "+2347012345678",
    "country": "Nigeria",
    "state": "Lagos",
    "city": "Ikeja",
    "preferred_language": "en",
    "secondary_languages": ["yo", "ig"],
    "consent_terms": true,
    "consent_hipaa": true,
    "consent_data_processing": true
  }' | python -m json.tool

# Check if the user exists and is an admin
echo -e "\n${BLUE}Checking if dr.emeka@example.com exists and is an admin${NC}"
curl -s "$BASE_URL/hospitals/admin/check-user/?email=dr.emeka@example.com" | python -m json.tool

# Scenario 3: Try to login with the new admin account
echo -e "\n${BLUE}Scenario 3: Login with the new admin account${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/token/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dr.emeka@example.com",
    "password": "secure123password"
  }')

# Extract access token
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access":"[^"]*' | cut -d'"' -f4)
echo "Access token obtained: ${ACCESS_TOKEN:0:20}... (truncated)"

# Scenario 4: Create a regular user that will later be converted to admin
echo -e "\n${BLUE}Scenario 4: Register a regular user${NC}"
curl -s -X POST "$BASE_URL/register/" \
  -H "Content-Type: application/json" \
  -d '{
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
    "consent_terms": true,
    "consent_hipaa": true,
    "consent_data_processing": true
  }' | python -m json.tool

# Check if the regular user exists but is not an admin
echo -e "\n${BLUE}Checking if dr.ngozi@example.com exists but is not an admin${NC}"
curl -s "$BASE_URL/hospitals/admin/check-user/?email=dr.ngozi@example.com" | python -m json.tool

# Scenario 5: Create a second hospital for the existing user
echo -e "\n${BLUE}Scenario 5: Creating a second test hospital${NC}"
HOSPITAL2_RESPONSE=$(curl -s -X POST "$BASE_URL/hospitals/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "Sunshine Medical Center",
    "address": "456 Health Avenue",
    "city": "Abuja",
    "state": "FCT",
    "country": "Nigeria",
    "postal_code": "90001",
    "registration_number": "SMC789012",
    "hospital_type": "private",
    "emergency_unit": true,
    "icu_unit": true,
    "email": "info@sunshinemedical.com",
    "phone": "+2348000000000"
  }')

# Extract hospital ID
HOSPITAL2_ID=$(echo $HOSPITAL2_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d":" -f2)
echo "Created second hospital with ID: $HOSPITAL2_ID"

# Scenario 6: Convert existing user to hospital admin
echo -e "\n${BLUE}Scenario 6: Convert existing user to hospital admin${NC}"
curl -s -X POST "$BASE_URL/hospitals/admin/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "existing_user": true,
    "user_email": "dr.ngozi@example.com",
    "hospital": '$HOSPITAL2_ID',
    "position": "Chief Medical Officer"
  }' | python -m json.tool

# Check if user is now an admin
echo -e "\n${BLUE}Checking if dr.ngozi@example.com is now an admin${NC}"
curl -s "$BASE_URL/hospitals/admin/check-user/?email=dr.ngozi@example.com" | python -m json.tool

# Scenario 7: Try to register an existing admin as admin again (should fail)
echo -e "\n${BLUE}Scenario 7: Try to register an existing admin as admin again (should fail)${NC}"
curl -s -X POST "$BASE_URL/hospitals/admin/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "existing_user": true,
    "user_email": "dr.emeka@example.com",
    "hospital": '$HOSPITAL2_ID',
    "position": "Consultant"
  }' | python -m json.tool

# Scenario 8: Test invalid data submission
echo -e "\n${BLUE}Scenario 8: Test invalid data submission${NC}"
curl -s -X POST "$BASE_URL/hospitals/admin/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "new.admin@example.com",
    "full_name": "New Admin",
    "password": "password123",
    "hospital": '$HOSPITAL_ID'
  }' | python -m json.tool

# Login with the second admin account
echo -e "\n${BLUE}Login with the second admin account${NC}"
LOGIN2_RESPONSE=$(curl -s -X POST "$BASE_URL/token/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dr.ngozi@example.com",
    "password": "secure456password"
  }')

# Extract second access token
ACCESS_TOKEN2=$(echo $LOGIN2_RESPONSE | grep -o '"access":"[^"]*' | cut -d'"' -f4)
echo "Second access token obtained: ${ACCESS_TOKEN2:0:20}... (truncated)"

# Scenario 9: Register a staff member with a hospital
echo -e "\n${BLUE}Scenario 9: Register a staff member with a hospital${NC}"
curl -s -X POST "$BASE_URL/hospitals/register/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN2" \
  -d '{
    "hospital": '$HOSPITAL_ID',
    "is_primary": true
  }' | python -m json.tool

# Scenario 10: View hospital staff registrations as admin
echo -e "\n${BLUE}Scenario 10: View hospital staff registrations as admin${NC}"
curl -s -X GET "$BASE_URL/hospitals/registrations/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python -m json.tool

# Find the latest registration ID
REGISTRATION_RESPONSE=$(curl -s -X GET "$BASE_URL/hospitals/registrations/" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
REGISTRATION_ID=$(echo $REGISTRATION_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d":" -f2)

# Scenario 11: Approve staff registration
echo -e "\n${BLUE}Scenario 11: Approve staff registration${NC}"
curl -s -X POST "$BASE_URL/hospitals/registrations/$REGISTRATION_ID/approve/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python -m json.tool

echo -e "\n${GREEN}All test scenarios completed!${NC}"
echo "==============================================" 