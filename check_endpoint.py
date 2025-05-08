#!/usr/bin/env python3
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import json

def check_endpoint():
    user = get_user_model().objects.get(email='eruwagolden@gmail.com')
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get('/api/patient/medical-record/summary/')
    print('Status code:', response.status_code)
    print(json.dumps(response.data, indent=2))

if __name__ == "__main__":
    check_endpoint() 