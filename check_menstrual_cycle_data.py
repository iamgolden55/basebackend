#!/usr/bin/env python
"""
Script to check menstrual cycle data for user eruwagolden@gmail.com
"""
import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from api.models import CustomUser, WomensHealthProfile, MenstrualCycle

def check_menstrual_cycle_data():
    """Check menstrual cycle data for eruwagolden@gmail.com"""
    target_email = "eruwagolden@gmail.com"
    
    print(f"=== Checking menstrual cycle data for {target_email} ===\n")
    
    try:
        # Find the user
        user = CustomUser.objects.get(email=target_email)
        print(f"Found user: {user.email}")
        print(f"User ID: {user.id}")
        print(f"User full name: {user.get_full_name()}")
        print(f"User created: {user.date_joined}")
        print()
        
        # Check if user has a women's health profile
        try:
            womens_profile = WomensHealthProfile.objects.get(user=user)
            print(f"Found women's health profile:")
            print(f"  Profile ID: {womens_profile.id}")
            print(f"  Profile created: {womens_profile.created_at}")
            print(f"  Average cycle length: {womens_profile.average_cycle_length}")
            print(f"  Average period duration: {womens_profile.average_period_duration}")
            print()
            
            # Get all menstrual cycles for this user
            cycles = MenstrualCycle.objects.filter(
                womens_health_profile=womens_profile
            ).order_by('-cycle_start_date')
            
            print(f"Found {cycles.count()} menstrual cycle(s):")
            print("=" * 50)
            
            for i, cycle in enumerate(cycles, 1):
                print(f"Cycle #{i}:")
                print(f"  ID: {cycle.id}")
                print(f"  Cycle start date: {cycle.cycle_start_date}")
                print(f"  Cycle end date: {cycle.cycle_end_date}")
                print(f"  Period end date: {cycle.period_end_date}")
                print(f"  Cycle length: {cycle.cycle_length}")
                print(f"  Period length: {cycle.period_length}")
                print(f"  Flow intensity: {cycle.flow_intensity}")
                print(f"  Is current cycle: {cycle.is_current_cycle}")
                print(f"  Created at: {cycle.created_at}")
                print(f"  Updated at: {cycle.updated_at}")
                print(f"  Notes: {cycle.notes}")
                print("-" * 30)
            
            if cycles.count() == 0:
                print("No menstrual cycles found for this user.")
            
        except WomensHealthProfile.DoesNotExist:
            print("No women's health profile found for this user.")
            
    except CustomUser.DoesNotExist:
        print(f"User with email {target_email} not found.")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_menstrual_cycle_data()