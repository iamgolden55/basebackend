"""
Test the appointment summary feature using Django directly.
This script should be run with: python manage.py shell < test_django_summary.py
"""

from api.models.user.custom_user import CustomUser
from api.models.medical.appointment import Appointment
from api.serializers import AppointmentSerializer, AppointmentListSerializer
import json

def print_separator():
    print("\n" + "="*80 + "\n")

def test_appointment_summary():
    # Find Al-Amin's user account
    user = CustomUser.objects.get(id=48)  # Al-Amin's user ID
    print(f"User: {user.first_name} {user.last_name} ({user.email})")
    
    # Get all of Al-Amin's appointments
    appointments = Appointment.objects.filter(patient=user).select_related(
        'doctor', 'doctor__user', 'hospital', 'department'
    ).order_by('appointment_date')
    
    print(f"Found {appointments.count()} appointments")
    print_separator()
    
    # List basic appointment info
    for i, appt in enumerate(appointments, 1):
        print(f"{i}. {appt.appointment_date.strftime('%Y-%m-%d %H:%M')} - "\
              f"{appt.department.name} with Dr. {appt.doctor.user.first_name} {appt.doctor.user.last_name} "\
              f"(ID: {appt.id}, Ref: {appt.appointment_id})")
    
    print_separator()
    
    # Choose one appointment to test
    if appointments.exists():
        # Select one appointment for detailed testing (using the first one as an example)
        test_appointment = appointments.first()
        print(f"Testing detailed summary for appointment {test_appointment.id} (Ref: {test_appointment.appointment_id})")
        
        # Test the detailed serializer
        serializer = AppointmentSerializer(test_appointment)
        serialized_data = serializer.data
        
        # Print formatted fields to test that they're working
        print("\nFormatted Fields Test:")
        formatted_fields = [
            'formatted_date', 
            'formatted_time', 
            'formatted_date_time',
            'doctor_full_name',
            'hospital_name',
            'department_name',
            'formatted_appointment_type',
            'formatted_priority',
            'important_notes'
        ]
        
        for field in formatted_fields:
            value = serialized_data.get(field, 'Not available')
            if isinstance(value, list):
                print(f"{field}:")
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"{field}: {value}")
        
        # Test summary structure (similar to what would be returned by the API endpoint)
        print("\nSummary Structure Test:")
        summary_data = {
            "appointment_details": {
                "appointment_id": test_appointment.appointment_id,
                "doctor": serialized_data.get('doctor_full_name'),
                "date": serialized_data.get('formatted_date'),
                "time": serialized_data.get('formatted_time'),
                "formatted_date_time": serialized_data.get('formatted_date_time'),
                "hospital": serialized_data.get('hospital_name'),
                "department": serialized_data.get('department_name'),
                "type": serialized_data.get('formatted_appointment_type'),
                "priority": serialized_data.get('formatted_priority'),
                "duration": f"{test_appointment.duration} minutes",
                "status": serialized_data.get('status_display'),
            },
            "patient_details": {
                "name": serialized_data.get('patient_name'),
                "chief_complaint": test_appointment.chief_complaint,
                "symptoms": test_appointment.symptoms,
                "medical_history": test_appointment.medical_history,
                "allergies": test_appointment.allergies,
                "current_medications": test_appointment.current_medications
            },
            "important_notes": serialized_data.get('important_notes'),
            "payment_info": {
                "payment_required": test_appointment.payment_required,
                "payment_status": test_appointment.payment_status,
                "is_insurance_based": test_appointment.is_insurance_based,
                "insurance_details": test_appointment.insurance_details if test_appointment.is_insurance_based else None
            },
            "additional_info": {
                "notes": test_appointment.notes,
                "created_at": test_appointment.created_at.strftime("%B %d, %Y at %I:%M %p") if test_appointment.created_at else None,
                "updated_at": test_appointment.updated_at.strftime("%B %d, %Y at %I:%M %p") if test_appointment.updated_at else None,
            }
        }
        
        print(json.dumps(summary_data, indent=2, default=str))
        
        # Test the email template context
        print("\nEmail Template Context Test:")
        email_context = {
            'patient_name': serialized_data.get('patient_name'),
            'appointment_id': test_appointment.appointment_id,
            'doctor_name': serialized_data.get('doctor_full_name'),
            'department_name': serialized_data.get('department_name'),
            'hospital_name': serialized_data.get('hospital_name'),
            'appointment_date': serialized_data.get('formatted_date_time'),
            'appointment_date_only': serialized_data.get('formatted_date'),
            'appointment_time_only': serialized_data.get('formatted_time'),
            'is_insurance_based': test_appointment.is_insurance_based,
            'payment_status': test_appointment.payment_status,
            'appointment_type': serialized_data.get('formatted_appointment_type'),
            'priority': serialized_data.get('formatted_priority'),
            'chief_complaint': test_appointment.chief_complaint,
            'calendar_link_included': True,
            'important_notes': serialized_data.get('important_notes'),
            'duration': serialized_data.get('appointment_duration_display')
        }
        
        print(json.dumps(email_context, indent=2, default=str))
        
        # Test the list serializer
        print("\nList Serializer Test:")
        list_serializer = AppointmentListSerializer(test_appointment)
        list_data = list_serializer.data
        
        # Check formatted fields in list view
        list_formatted_fields = [
            'formatted_date', 
            'formatted_time', 
            'formatted_date_time',
            'doctor_full_name',
            'hospital_name',
            'department_name',
            'formatted_appointment_type',
            'formatted_priority'
        ]
        
        print("List view formatted fields:")
        for field in list_formatted_fields:
            value = list_data.get(field, 'Not available')
            print(f"  - {field}: {value}")
        
        # Create a sample list output as it would appear in the API
        sample_list_item = {
            "id": list_data.get('id'),
            "appointment_id": list_data.get('appointment_id'),
            "doctor_full_name": list_data.get('doctor_full_name'),
            "hospital_name": list_data.get('hospital_name'),
            "department_name": list_data.get('department_name'),
            "formatted_date_time": list_data.get('formatted_date_time'),
            "formatted_appointment_type": list_data.get('formatted_appointment_type'),
            "status_display": list_data.get('status_display'),
            "chief_complaint": list_data.get('chief_complaint')
        }
        
        print("\nSample list item:")
        print(json.dumps(sample_list_item, indent=2, default=str))
        
    else:
        print("No appointments found for testing.")

# Run the test
print_separator()
print("APPOINTMENT SUMMARY FEATURE TEST")
print_separator()
test_appointment_summary() 