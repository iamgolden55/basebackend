#!/usr/bin/env python3
import os
import logging
import sys

# Configure logging to print to stdout
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import json

def test_with_logging():
    print("Checking endpoint with logging...")
    
    # Set Django logger to DEBUG
    django_logger = logging.getLogger('django')
    django_logger.setLevel(logging.DEBUG)
    
    # Get API logger
    api_logger = logging.getLogger('api')
    api_logger.setLevel(logging.DEBUG)
    
    try:
        # Get the user
        User = get_user_model()
        user = User.objects.get(email='eruwagolden@gmail.com')
        
        # Create API client
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Make the request
        print("Making request to /api/patient/medical-record/summary/")
        response = client.get('/api/patient/medical-record/summary/')
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print("Response received successfully")
            data = response.data
            
            # Check if interactions exist
            if 'data' in data and 'interactions' in data['data']:
                interactions = data['data']['interactions']
                print(f"Found {len(interactions)} doctor interactions")
                
                if interactions:
                    latest = interactions[0]
                    print(f"Latest interaction date: {latest['formatted_date']}")
                    print(f"Doctor: {latest['doctor_name']}")
                    print(f"Interaction type: {latest['interaction_type']}")
                else:
                    print("No interactions found - this should be investigated")
            else:
                print("Response doesn't contain interactions data:")
                print(json.dumps(data, indent=2))
        else:
            print(f"Error response: {response.data}")
        
    except Exception as e:
        print(f"Error testing endpoint: {str(e)}")

if __name__ == "__main__":
    test_with_logging() 