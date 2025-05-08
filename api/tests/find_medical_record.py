#!/usr/bin/env python
import os
import sys
import django
import json
from datetime import datetime
from pprint import pprint

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

# Import models after setting up Django
from api.models.medical.medical_record import MedicalRecord
from api.models.user.custom_user import CustomUser
from django.db.models import Q

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def find_medical_records(query):
    """
    Find medical records by patient name, email, or ID
    Returns summary list of matching records
    """
    results = []
    
    # First try to find by user ID (exact match)
    try:
        if query.isdigit():
            user_id = int(query)
            user = CustomUser.objects.filter(id=user_id).first()
            if user and hasattr(user, 'medical_record'):
                record = user.medical_record
                results.append({
                    "hpn": record.hpn,
                    "user_id": user.id,
                    "name": f"{user.first_name} {user.last_name}",
                    "email": user.email,
                    "match_type": "User ID exact match"
                })
    except:
        pass
        
    # Try to match by email
    users = CustomUser.objects.filter(email__icontains=query)
    for user in users:
        if hasattr(user, 'medical_record') and user.medical_record:
            record = user.medical_record
            if not any(r['hpn'] == record.hpn for r in results):  # Avoid duplicates
                results.append({
                    "hpn": record.hpn,
                    "user_id": user.id,
                    "name": f"{user.first_name} {user.last_name}",
                    "email": user.email,
                    "match_type": "Email match"
                })
    
    # Try to match by name (first or last)
    name_users = CustomUser.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query)
    )
    for user in name_users:
        if hasattr(user, 'medical_record') and user.medical_record:
            record = user.medical_record
            if not any(r['hpn'] == record.hpn for r in results):  # Avoid duplicates
                results.append({
                    "hpn": record.hpn,
                    "user_id": user.id,
                    "name": f"{user.first_name} {user.last_name}",
                    "email": user.email,
                    "match_type": "Name match"
                })
    
    # Try to match by HPN (exact match)
    try:
        record = MedicalRecord.objects.filter(hpn=query).first()
        if record and not any(r['hpn'] == record.hpn for r in results):  # Avoid duplicates
            results.append({
                "hpn": record.hpn,
                "user_id": record.user.id if record.user else "Anonymous",
                "name": f"{record.user.first_name} {record.user.last_name}" if record.user else "Anonymous",
                "email": record.user.email if record.user else "Anonymous",
                "match_type": "HPN exact match"
            })
    except:
        pass
    
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python find_medical_record.py [search term]")
        print("Search by patient name, email, ID, or HPN number")
        sys.exit(1)
    
    search_term = sys.argv[1]
    print(f"Searching for: {search_term}")
    
    results = find_medical_records(search_term)
    
    if not results:
        print("No medical records found matching your search.")
    else:
        print(f"Found {len(results)} matching medical records:")
        for idx, record in enumerate(results, 1):
            print(f"\n{idx}. HPN: {record['hpn']}")
            print(f"   Patient: {record['name']}")
            print(f"   Email: {record['email']}")
            print(f"   User ID: {record['user_id']}")
            print(f"   Match type: {record['match_type']}")
        
        print("\nFor complete details of a specific record, use:")
        print("python get_medical_records_by_hpn.py [HPN]") 