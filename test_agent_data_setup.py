#!/usr/bin/env python
"""
Test Data Setup Script for Women's Health Agents

This script creates comprehensive test data for testing all agent functionalities.
Run this script to populate the database with realistic test data.

Usage:
    python test_agent_data_setup.py

Note: This script should be run in a test environment only.
"""

import os
import sys
import django
from datetime import datetime, timedelta, date
import random
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import (
    WomensHealthProfile, MenstrualCycle, DailyHealthLog, 
    FertilityTracking, HealthGoal, PregnancyRecord, HealthScreening
)

User = get_user_model()


class AgentTestDataSetup:
    """Class to set up comprehensive test data for agent testing."""
    
    def __init__(self):
        self.users_created = []
        self.profiles_created = []
        
    def create_test_users(self):
        """Create test users with different data profiles."""
        print("Creating test users...")
        
        # User 1: Complete data for full testing
        user1, created = User.objects.get_or_create(
            email='test_user_1@example.com',
            defaults={
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'womens_health_verified': True,
                'is_active': True
            }
        )
        if created:
            user1.set_password('testpass123')
            user1.save()
        self.users_created.append(user1)
        
        # User 2: Minimal data for insufficient data testing
        user2, created = User.objects.get_or_create(
            email='test_user_2@example.com',
            defaults={
                'first_name': 'Betty',
                'last_name': 'Wilson',
                'womens_health_verified': True,
                'is_active': True
            }
        )
        if created:
            user2.set_password('testpass123')
            user2.save()
        self.users_created.append(user2)
        
        # User 3: Risk factors for clinical testing
        user3, created = User.objects.get_or_create(
            email='test_user_3@example.com',
            defaults={
                'first_name': 'Carol',
                'last_name': 'Davis',
                'womens_health_verified': True,
                'is_active': True
            }
        )
        if created:
            user3.set_password('testpass123')
            user3.save()
        self.users_created.append(user3)
        
        print(f"Created {len(self.users_created)} test users")
        return self.users_created
    
    def create_womens_health_profiles(self):
        """Create women's health profiles for test users."""
        print("Creating women's health profiles...")
        
        for i, user in enumerate(self.users_created):
            # Generate age-appropriate birth dates
            ages = [28, 22, 35]  # Different ages for different test scenarios
            birth_date = date.today() - timedelta(days=ages[i] * 365)
            
            profile, created = WomensHealthProfile.objects.get_or_create(
                user=user,
                defaults={
                    'average_cycle_length': random.randint(25, 32),
                    'average_period_duration': random.randint(3, 7),
                    'pregnancy_status': 'not_pregnant'
                }
            )
            
            self.profiles_created.append(profile)
            if created:
                print(f"Created new profile for {user.email}")
            else:
                print(f"Using existing profile for {user.email}")
        
        print(f"Created {len(self.profiles_created)} health profiles")
        return self.profiles_created
    
    def create_menstrual_cycles(self, profile, cycle_count=8):
        """Create menstrual cycle data for testing."""
        # Clear existing cycles for this profile to avoid duplicates
        MenstrualCycle.objects.filter(womens_health_profile=profile).delete()
        
        cycles = []
        
        # Start from 8 months ago for realistic data
        start_date = timezone.now().date() - timedelta(days=cycle_count * 30)
        
        for i in range(cycle_count):
            # Vary cycle characteristics for realistic data
            base_cycle_length = 28
            variation = random.randint(-3, 3)
            cycle_length = max(21, min(35, base_cycle_length + variation))
            
            cycle_start = start_date + timedelta(days=sum([
                28 + random.randint(-3, 3) for _ in range(i)
            ]))
            
            cycle = MenstrualCycle.objects.create(
                womens_health_profile=profile,
                cycle_start_date=cycle_start,
                cycle_length=cycle_length,
                flow_intensity=random.choice(['light', 'medium', 'heavy']),
                period_length=random.randint(3, 7),
                is_regular=random.choice([True, True, False]),  # 67% regular
                cycle_quality_score=random.randint(6, 10)
            )
            cycles.append(cycle)
        
        return cycles
    
    def create_daily_health_logs(self, profile, log_count=60):
        """Create daily health log data for testing."""
        # Clear existing logs for this profile to avoid duplicates
        DailyHealthLog.objects.filter(womens_health_profile=profile).delete()
        
        logs = []
        start_date = timezone.now().date() - timedelta(days=log_count)
        
        moods = ['happy', 'neutral', 'sad', 'anxious', 'energetic', 'tired', 'stressed']
        symptom_options = [
            ['bloating', 'cramps'],
            ['headache'],
            ['mood_swings', 'fatigue'],
            ['breast_tenderness'],
            ['acne', 'bloating'],
            ['insomnia'],
            ['back_pain', 'fatigue'],
            []  # No symptoms
        ]
        
        for i in range(log_count):
            log_date = start_date + timedelta(days=i)
            
            log = DailyHealthLog.objects.create(
                womens_health_profile=profile,
                date=log_date,
                water_intake_liters=round(random.uniform(1.5, 3.5), 1),
                sleep_duration_hours=round(random.uniform(6.0, 9.0), 1),
                weight_kg=round(random.uniform(50.0, 80.0), 1)
            )
            logs.append(log)
        
        return logs
    
    def create_fertility_tracking(self, profile, entry_count=15):
        """Create fertility tracking data."""
        # Clear existing fertility tracking for this profile to avoid duplicates
        FertilityTracking.objects.filter(womens_health_profile=profile).delete()
        
        entries = []
        start_date = timezone.now().date() - timedelta(days=entry_count * 2)
        
        for i in range(entry_count):
            tracking_date = start_date + timedelta(days=i * 2)
            
            entry = FertilityTracking.objects.create(
                womens_health_profile=profile,
                date=tracking_date,
                basal_body_temperature=round(36.5 + random.uniform(0, 1.0), 2),
                cycle_day=random.randint(1, 28)
            )
            entries.append(entry)
        
        return entries
    
    def create_health_goals(self, profile):
        """Create health goals for testing."""
        goals = []
        
        goal_types = [
            {
                'title': 'Daily Water Intake',
                'description': 'Drink at least 8 glasses of water daily',
                'target_value': 8,
                'target_unit': 'glasses',
                'goal_type': 'hydration'
            },
            {
                'title': 'Exercise Routine',
                'description': 'Exercise for at least 30 minutes daily',
                'target_value': 30,
                'target_unit': 'minutes',
                'goal_type': 'exercise'
            },
            {
                'title': 'Sleep Quality',
                'description': 'Get 7-8 hours of quality sleep nightly',
                'target_value': 8,
                'target_unit': 'hours',
                'goal_type': 'sleep'
            }
        ]
        
        for goal_data in goal_types:
            goal = HealthGoal.objects.create(
                womens_health_profile=profile,
                title=goal_data['title'],
                description=goal_data['description'],
                category=goal_data['goal_type'],
                start_date=timezone.now().date(),
                target_date=timezone.now().date() + timedelta(days=90)
            )
            goals.append(goal)
        
        return goals
    
    def create_health_screenings(self, profile):
        """Create health screening records."""
        screenings = []
        
        screening_types = [
            {
                'screening_type': 'cervical_cancer_screening',
                'date': timezone.now().date() - timedelta(days=365),
                'result': 'normal',
                'notes': 'Annual Pap smear - results normal'
            },
            {
                'screening_type': 'blood_pressure_check',
                'date': timezone.now().date() - timedelta(days=90),
                'result': 'normal',
                'notes': 'Blood pressure: 120/80 mmHg'
            },
            {
                'screening_type': 'cholesterol_screening',
                'date': timezone.now().date() - timedelta(days=180),
                'result': 'normal',
                'notes': 'Total cholesterol: 180 mg/dL'
            }
        ]
        
        for screening_data in screening_types:
            screening = HealthScreening.objects.create(
                womens_health_profile=profile,
                screening_type=screening_data['screening_type'],
                completed_date=screening_data['date'],
                result_status=screening_data['result']
            )
            screenings.append(screening)
        
        return screenings
    
    def create_test_data_user_1(self):
        """Create comprehensive test data for User 1 (complete data)."""
        print("Creating comprehensive data for User 1...")
        user = self.users_created[0]
        profile = self.profiles_created[0]
        
        # Create 8 menstrual cycles (sufficient for analysis)
        cycles = self.create_menstrual_cycles(profile, 8)
        print(f"Created {len(cycles)} menstrual cycles for User 1")
        
        # Create 60 days of health logs
        logs = self.create_daily_health_logs(profile, 60)
        print(f"Created {len(logs)} daily health logs for User 1")
        
        # Create fertility tracking data
        fertility_entries = self.create_fertility_tracking(profile, 15)
        print(f"Created {len(fertility_entries)} fertility tracking entries for User 1")
        
        # Create health goals
        goals = self.create_health_goals(profile)
        print(f"Created {len(goals)} health goals for User 1")
        
        # Create health screenings
        screenings = self.create_health_screenings(profile)
        print(f"Created {len(screenings)} health screenings for User 1")
    
    def create_test_data_user_2(self):
        """Create minimal test data for User 2 (insufficient data testing)."""
        print("Creating minimal data for User 2...")
        user = self.users_created[1]
        profile = self.profiles_created[1]
        
        # Create only 1 menstrual cycle (insufficient for analysis)
        cycles = self.create_menstrual_cycles(profile, 1)
        print(f"Created {len(cycles)} menstrual cycle for User 2")
        
        # Create only 5 days of health logs
        logs = self.create_daily_health_logs(profile, 5)
        print(f"Created {len(logs)} daily health logs for User 2")
    
    def create_test_data_user_3(self):
        """Create risk factor data for User 3 (clinical testing)."""
        print("Creating risk factor data for User 3...")
        user = self.users_created[2]
        profile = self.profiles_created[2]
        
        # Create 12 menstrual cycles with some irregularities
        cycles = []
        start_date = timezone.now().date() - timedelta(days=365)
        
        for i in range(12):
            # Create some irregular cycles
            if i % 4 == 0:  # Every 4th cycle is irregular
                cycle_length = random.choice([18, 45])  # Very short or very long
            else:
                cycle_length = random.randint(26, 32)  # Normal variation
            
            cycle_start = start_date + timedelta(days=sum([
                28 + random.randint(-3, 3) for _ in range(i)
            ]))
            
            cycle = MenstrualCycle.objects.create(
                womens_health_profile=profile,
                cycle_start_date=cycle_start,
                cycle_length=cycle_length,
                flow_intensity=random.choice(['light', 'medium', 'heavy']),
                period_length=random.randint(3, 7),
                is_regular=cycle_length in [26, 27, 28, 29, 30, 31, 32],
                cycle_quality_score=random.randint(3, 7)  # Lower quality for irregular cycles
            )
            cycles.append(cycle)
        
        print(f"Created {len(cycles)} menstrual cycles (with irregularities) for User 3")
        
        # Create 90 days of health logs with mood variability
        logs = []
        start_date = timezone.now().date() - timedelta(days=90)
        
        high_variability_moods = ['anxious', 'sad', 'stressed', 'happy', 'energetic']
        symptom_options = [
            ['mood_swings', 'fatigue', 'bloating'],
            ['headache', 'cramps'],
            ['breast_tenderness', 'acne'],
            ['insomnia', 'back_pain'],
            ['fatigue', 'mood_swings']
        ]
        
        for i in range(90):
            log_date = start_date + timedelta(days=i)
            
            log = DailyHealthLog.objects.create(
                womens_health_profile=profile,
                date=log_date,
                water_intake_liters=round(random.uniform(1.0, 3.0), 1),
                sleep_duration_hours=round(random.uniform(4.0, 9.0), 1),
                weight_kg=round(random.uniform(55.0, 75.0), 1)
            )
            logs.append(log)
        
        print(f"Created {len(logs)} daily health logs (with high mood variability) for User 3")
        
        # Create health goals and screenings
        goals = self.create_health_goals(profile)
        screenings = self.create_health_screenings(profile)
        print(f"Created {len(goals)} health goals and {len(screenings)} screenings for User 3")
    
    def create_admin_user(self):
        """Create an admin user for testing performance endpoints."""
        print("Creating admin user...")
        
        admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        
        print(f"Admin user created: {admin_user.email}")
        return admin_user
    
    def setup_all_test_data(self):
        """Set up all test data for agent testing."""
        print("="*50)
        print("WOMEN'S HEALTH AGENTS - TEST DATA SETUP")
        print("="*50)
        
        # Create users and profiles
        self.create_test_users()
        self.create_womens_health_profiles()
        
        # Create admin user
        self.create_admin_user()
        
        # Create test data for each user
        self.create_test_data_user_1()
        self.create_test_data_user_2()
        self.create_test_data_user_3()
        
        print("\n" + "="*50)
        print("TEST DATA SETUP COMPLETED SUCCESSFULLY!")
        print("="*50)
        
        # Print summary
        print("\nTest Users Created:")
        for i, user in enumerate(self.users_created, 1):
            print(f"  User {i}: {user.email} (ID: {user.id})")
        
        print(f"\nAdmin User: admin@example.com")
        
        print(f"\nData Summary:")
        print(f"  - User 1: Complete data (8 cycles, 60 health logs)")
        print(f"  - User 2: Minimal data (1 cycle, 5 health logs)")
        print(f"  - User 3: Risk factors (12 irregular cycles, 90 mood logs)")
        
        print(f"\nReady for testing! Use these endpoints:")
        print(f"  - Analytics: /api/agents/analytics/")
        print(f"  - Performance: /api/agents/performance/ (admin only)")
        print(f"  - Clinical: /api/agents/clinical/")
        
        return {
            'users': self.users_created,
            'profiles': self.profiles_created,
            'admin_user': User.objects.get(email='admin@example.com')
        }
    
    def cleanup_test_data(self):
        """Clean up test data (use with caution!)."""
        print("WARNING: This will delete all test data!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        
        if response.lower() == 'yes':
            # Delete test users and related data
            test_emails = [
                'test_user_1@example.com',
                'test_user_2@example.com', 
                'test_user_3@example.com',
                'admin@example.com'
            ]
            
            deleted_count = User.objects.filter(email__in=test_emails).delete()[0]
            print(f"Deleted {deleted_count} test users and all related data")
        else:
            print("Cleanup cancelled")


def main():
    """Main function to run the test data setup."""
    setup = AgentTestDataSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'cleanup':
        setup.cleanup_test_data()
    else:
        setup.setup_all_test_data()


if __name__ == '__main__':
    main()