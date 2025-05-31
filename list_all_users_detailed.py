#!/usr/bin/env python3
"""
🏥 Hospital Management System - Complete User Database Report
Created by Codey - Your Friendly Python Tutor! 🚀

This script provides a comprehensive overview of ALL users in the system.
"""

import os
import django
import sys
from django.utils import timezone
from datetime import datetime

# Setup Django environment
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.models import CustomUser, Hospital, HospitalRegistration

def print_separator(title=""):
    """Print a fancy separator"""
    print("=" * 80)
    if title:
        print(f"  {title}".center(80))
        print("=" * 80)

def print_user_summary():
    """Print overall user statistics"""
    print_separator("🏥 HOSPITAL MANAGEMENT SYSTEM - USER DATABASE REPORT")
    
    total_users = CustomUser.objects.count()
    verified_users = CustomUser.objects.filter(is_verified=True).count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    
    print(f"📊 OVERALL STATISTICS:")
    print(f"   Total Users: {total_users}")
    print(f"   Verified Users: {verified_users}")
    print(f"   Active Users: {active_users}")
    print(f"   Email Verified: {CustomUser.objects.filter(is_email_verified=True).count()}")
    print()

def print_role_breakdown():
    """Print users by role"""
    print_separator("👥 USERS BY ROLE")
    
    # Get all unique roles
    roles = CustomUser.objects.values_list('role', flat=True).distinct()
    
    for role in sorted(roles):
        count = CustomUser.objects.filter(role=role).count()
        role_display = dict(CustomUser.ROLES).get(role, role.title())
        print(f"   {role_display}: {count} users")
    print()

def print_detailed_user_list():
    """Print detailed information for each user"""
    print_separator("📋 DETAILED USER LIST")
    
    users = CustomUser.objects.all().order_by('role', 'first_name', 'last_name')
    
    current_role = None
    for user in users:
        # Print role header when role changes
        if user.role != current_role:
            current_role = user.role
            role_display = dict(CustomUser.ROLES).get(user.role, user.role.title())
            print(f"\n🏷️  {role_display.upper()} ({CustomUser.objects.filter(role=user.role).count()} users)")
            print("-" * 60)
        
        # Basic user info
        print(f"👤 {user.first_name} {user.last_name}")
        print(f"   📧 Email: {user.email}")
        print(f"   🆔 HPN: {user.hpn or 'Not generated'}")
        print(f"   📱 Phone: {user.phone or 'Not provided'}")
        
        # Status indicators
        status_indicators = []
        if user.is_verified: status_indicators.append("✅ Verified")
        if user.is_email_verified: status_indicators.append("📧 Email OK")
        if user.is_active: status_indicators.append("🟢 Active")
        if user.is_staff: status_indicators.append("⚙️ Staff")
        if user.is_superuser: status_indicators.append("👑 Admin")
        
        if status_indicators:
            print(f"   Status: {' | '.join(status_indicators)}")
        
        # Personal info
        if user.date_of_birth:
            age = (datetime.now().date() - user.date_of_birth).days // 365
            print(f"   🎂 Age: {age} years")
        if user.gender:
            print(f"   ⚤ Gender: {user.gender.title()}")
        if user.city or user.state or user.country:
            location = ", ".join(filter(None, [user.city, user.state, user.country]))
            print(f"   📍 Location: {location}")
        
        # Hospital registration
        if user.hospital:
            print(f"   🏥 Primary Hospital: {user.hospital.name}")
        
        # Registration details
        registrations = HospitalRegistration.objects.filter(user=user)
        if registrations.exists():
            approved_regs = registrations.filter(status='approved')
            pending_regs = registrations.filter(status='pending')
            
            if approved_regs.exists():
                print(f"   ✅ Registered at: {', '.join([reg.hospital.name for reg in approved_regs])}")
            if pending_regs.exists():
                print(f"   ⏳ Pending at: {', '.join([reg.hospital.name for reg in pending_regs])}")
        
        # Join date
        print(f"   📅 Joined: {user.date_joined.strftime('%Y-%m-%d %H:%M')}")
        print()

def print_hospital_breakdown():
    """Print users by hospital"""
    print_separator("🏥 USERS BY HOSPITAL")
    
    hospitals = Hospital.objects.all()
    
    for hospital in hospitals:
        # Users with this as primary hospital
        primary_users = CustomUser.objects.filter(hospital=hospital).count()
        
        # All approved registrations at this hospital
        approved_registrations = HospitalRegistration.objects.filter(
            hospital=hospital, 
            status='approved'
        ).count()
        
        # Pending registrations
        pending_registrations = HospitalRegistration.objects.filter(
            hospital=hospital, 
            status='pending'
        ).count()
        
        print(f"🏥 {hospital.name}")
        print(f"   Primary Users: {primary_users}")
        print(f"   Total Approved: {approved_registrations}")
        print(f"   Pending: {pending_registrations}")
        print()

def print_recent_activity():
    """Print recent user activity"""
    print_separator("🕒 RECENT ACTIVITY (Last 7 Days)")
    
    from datetime import timedelta
    
    week_ago = timezone.now() - timedelta(days=7)
    
    recent_users = CustomUser.objects.filter(
        date_joined__gte=week_ago
    ).order_by('-date_joined')
    
    recent_registrations = HospitalRegistration.objects.filter(
        created_at__gte=week_ago
    ).order_by('-created_at')
    
    print(f"📈 New Users (Last 7 days): {recent_users.count()}")
    for user in recent_users[:5]:  # Show last 5
        print(f"   👤 {user.first_name} {user.last_name} ({user.role}) - {user.date_joined.strftime('%Y-%m-%d')}")
    
    if recent_users.count() > 5:
        print(f"   ... and {recent_users.count() - 5} more")

    print(f"\n🏥 New Registrations (Last 7 days): {recent_registrations.count()}")
    for reg in recent_registrations[:5]:  # Show last 5
        print(f"   👤 {reg.user.first_name} {reg.user.last_name} → {reg.hospital.name} - {reg.created_at.strftime('%Y-%m-%d')}")
    
    if recent_registrations.count() > 5:
        print(f"   ... and {recent_registrations.count() - 5} more")
    print()

def main():
    """Main execution function"""
    try:
        print("\n🚀 Generating comprehensive user database report...")
        print("   This might take a moment for large databases...\n")
        
        # Run all reports
        print_user_summary()
        print_role_breakdown()
        print_hospital_breakdown()
        print_recent_activity()
        print_detailed_user_list()
        
        print_separator("✅ REPORT COMPLETE")
        print("🎉 User database report generated successfully!")
        print("💡 Tip: You can pipe this output to a file using: python list_all_users_detailed.py > user_report.txt")
        
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
