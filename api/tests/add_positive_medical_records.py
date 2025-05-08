#!/usr/bin/env python
import os
import sys
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# Import models after Django setup
from api.models import CustomUser, Doctor
from api.models.medical.medical_record import MedicalRecord, PatientDiagnosis, PatientTreatment, DoctorInteraction

def generate_date_in_past(days_ago):
    return timezone.now() - timedelta(days=random.randint(1, days_ago))

def main():
    # Get user by email
    email = 'eruwagolden55@gmail.com'
    try:
        user = CustomUser.objects.get(email=email)
        print(f"Found user: {user.email} (ID: {user.id})")
    except CustomUser.DoesNotExist:
        print(f"User with email {email} not found.")
        return

    # Get or create medical record
    try:
        medical_record = user.medical_record
        print(f"Using existing medical record with HPN: {medical_record.hpn}")
        
        # Update basic medical information for existing record
        medical_record.blood_type = random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'])
        medical_record.allergies = "No known allergies"
        medical_record.chronic_conditions = "Mild seasonal allergies, well-controlled with occasional antihistamines. Mild myopia, corrected with prescription glasses. Occasional tension headaches, managed with proper rest and hydration."
        medical_record.emergency_contact_name = "Jane Doe"
        medical_record.emergency_contact_phone = "+234 800 555 1234"
        medical_record.is_high_risk = False
        medical_record.save()
        print("Updated basic medical information")
    except:
        # Create new medical record with the user's ID as the HPN
        hpn = f"PHB-{user.id:05d}"
        medical_record = MedicalRecord.objects.create(
            user=user,
            hpn=hpn,
            blood_type=random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
            allergies="No known allergies",
            chronic_conditions="Mild seasonal allergies, well-controlled with occasional antihistamines. Mild myopia, corrected with prescription glasses. Occasional tension headaches, managed with proper rest and hydration.",
            is_high_risk=False,
            last_visit_date=timezone.now(),
        )
        print(f"Created new medical record with HPN: {medical_record.hpn}")

    # Get some doctors for diagnoses and treatments
    doctors = list(Doctor.objects.all()[:5])
    if not doctors:
        print("No doctors found in the system. Cannot add records.")
        return
    
    # Clear any existing diagnoses, treatments, and interactions
    PatientDiagnosis.objects.filter(medical_record=medical_record).delete()
    PatientTreatment.objects.filter(medical_record=medical_record).delete()
    DoctorInteraction.objects.filter(medical_record=medical_record).delete()
    print("Cleared existing medical data")

    # Add positive diagnoses (health checkups with good results)
    positive_diagnoses = [
        {
            "code": "Z00.00", 
            "name": "Routine health checkup - all findings normal",
            "is_chronic": False,
            "severity_rating": 1,
            "notes": "Annual checkup completed. All vitals are within normal range. Patient exhibits excellent health."
        },
        {
            "code": "J30.1", 
            "name": "Allergic rhinitis due to pollen",
            "is_chronic": True,
            "severity_rating": 2,
            "notes": "Seasonal allergies well-controlled with occasional over-the-counter antihistamines. Patient reports significant improvement in symptoms with current management."
        },
        {
            "code": "H52.1", 
            "name": "Myopia",
            "is_chronic": True,
            "severity_rating": 1,
            "notes": "Mild myopia, stable for past 2 years. Vision corrected to 20/20 with prescription glasses. Annual eye exam recommended."
        },
        {
            "code": "G44.2", 
            "name": "Tension-type headache",
            "is_chronic": True,
            "severity_rating": 1,
            "notes": "Occasional tension headaches related to stress. Managed effectively with rest, hydration, and relaxation techniques. No medication required."
        },
        {
            "code": "Z71.3", 
            "name": "Dietary counseling and surveillance",
            "is_chronic": False,
            "severity_rating": 1,
            "notes": "Patient maintains a balanced diet. Recommended to continue current nutritional habits."
        },
        {
            "code": "Z71.82", 
            "name": "Exercise counseling",
            "is_chronic": False,
            "severity_rating": 1,
            "notes": "Patient exercises regularly. Maintaining current exercise regimen is advised."
        },
        {
            "code": "Z01.419", 
            "name": "Encounter for routine eye examination - normal findings",
            "is_chronic": False,
            "severity_rating": 1,
            "notes": "Vision 20/20. No signs of eye strain or deterioration."
        },
        {
            "code": "Z01.30", 
            "name": "Encounter for routine dental examination - normal findings",
            "is_chronic": False,
            "severity_rating": 1,
            "notes": "Excellent dental hygiene. No cavities or gum disease."
        },
        {
            "code": "Z01.810", 
            "name": "Encounter for routine cardiovascular examination - normal findings",
            "is_chronic": False,
            "severity_rating": 1,
            "notes": "Heart function is excellent. Blood pressure and cholesterol levels are optimal."
        },
    ]

    for diagnosis in positive_diagnoses:
        diagnosis_date = generate_date_in_past(180)  # Within last 6 months
        PatientDiagnosis.objects.create(
            medical_record=medical_record,
            diagnosis_code=diagnosis["code"],
            diagnosis_name=diagnosis["name"],
            diagnosis_date=diagnosis_date,
            diagnosed_by=random.choice(doctors),
            is_chronic=diagnosis["is_chronic"],
            is_active=True,
            severity_rating=diagnosis["severity_rating"],
            notes=diagnosis["notes"]
        )
    
    print(f"Added {len(positive_diagnoses)} positive diagnoses")

    # Add preventive treatments and health advice
    positive_treatments = [
        {
            "type": "medication",
            "name": "Multivitamin supplement",
            "code": "PREV-001",
            "dosage": "1 tablet",
            "frequency": "Daily",
            "notes": "General wellness supplement to maintain optimal vitamin levels."
        },
        {
            "type": "therapy",
            "name": "Fitness training program",
            "code": "FIT-PROG",
            "dosage": None,
            "frequency": "3 times per week",
            "notes": "Customized fitness program aimed at maintaining cardiovascular health and muscle tone."
        },
        {
            "type": "therapy",
            "name": "Stress management techniques",
            "code": "STRS-MGT",
            "dosage": None,
            "frequency": "As needed",
            "notes": "Breathing exercises and mindfulness techniques for general wellbeing."
        },
        {
            "type": "medication",
            "name": "Vitamin D supplement",
            "code": "VIT-D",
            "dosage": "1000 IU",
            "frequency": "Daily",
            "notes": "Maintaining bone health and immune system function."
        },
        {
            "type": "other",
            "name": "Hydration reminders",
            "code": "HYDRO-1",
            "dosage": "8-10 glasses",
            "frequency": "Daily",
            "notes": "Keeping well hydrated for optimal organ function and skin health."
        },
    ]

    for treatment in positive_treatments:
        start_date = generate_date_in_past(90)  # Within last 3 months
        PatientTreatment.objects.create(
            medical_record=medical_record,
            treatment_type=treatment["type"],
            treatment_name=treatment["name"],
            treatment_code=treatment["code"],
            prescribed_by=random.choice(doctors),
            start_date=start_date,
            end_date=None if random.choice([True, False]) else start_date + timedelta(days=random.randint(10, 30)),
            is_active=True,
            dosage=treatment["dosage"],
            frequency=treatment["frequency"],
            notes=treatment["notes"]
        )
    
    print(f"Added {len(positive_treatments)} positive treatments")

    # Add doctor interactions (all positive)
    interaction_types = ['appointment', 'consultation', 'follow_up']
    
    for i in range(10):
        interaction_date = generate_date_in_past(365)  # Within the last year
        DoctorInteraction.objects.create(
            medical_record=medical_record,
            doctor=random.choice(doctors),
            interaction_date=interaction_date,
            interaction_type=random.choice(interaction_types),
            patient_rating=random.randint(4, 5),  # High ratings (positive)
            doctor_notes=random.choice([
                "Patient is maintaining excellent health. No concerns.",
                "Routine check-up shows all parameters within normal range.",
                "Patient follows all health recommendations diligently.",
                "Excellent progress on preventative health measures.",
                "Patient demonstrates exemplary self-care habits."
            ]),
            communication_issues=False
        )
    
    print("Added 10 positive doctor interactions")
    
    # Update medical record complexity metrics
    medical_record.update_complexity_metrics()
    medical_record.last_visit_date = generate_date_in_past(30)  # Recent visit
    medical_record.save()
    
    print(f"Successfully updated medical record for {user.email}")
    print(f"Comorbidity count: {medical_record.comorbidity_count}")
    print(f"Medication count: {medical_record.medication_count}")
    print(f"Care plan complexity: {medical_record.care_plan_complexity}")

if __name__ == "__main__":
    main() 