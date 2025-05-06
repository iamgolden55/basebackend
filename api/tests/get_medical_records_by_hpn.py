#!/usr/bin/env python
import os
import sys
import django
from pprint import pprint

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

# Import models after setting up Django
from api.models.medical.medical_record import MedicalRecord, PatientDiagnosis, PatientTreatment, DoctorInteraction

def get_medical_record_by_hpn(hpn):
    """Retrieve a comprehensive medical record by HPN number"""
    try:
        # Get the main medical record
        record = MedicalRecord.objects.get(hpn=hpn)
        
        # Basic medical record information
        record_data = {
            "hpn": record.hpn,
            "patient_id": record.user.id if record.user else "Anonymous",
            "patient_name": f"{record.user.first_name} {record.user.last_name}" if record.user else "Anonymous",
            "blood_type": record.blood_type,
            "allergies": record.allergies,
            "chronic_conditions": record.chronic_conditions,
            "emergency_contact": {
                "name": record.emergency_contact_name,
                "phone": record.emergency_contact_phone
            },
            "is_high_risk": record.is_high_risk,
            "last_visit_date": record.last_visit_date,
            "complexity_metrics": {
                "comorbidity_count": record.comorbidity_count,
                "hospitalization_count": record.hospitalization_count,
                "last_hospitalization_date": record.last_hospitalization_date,
                "care_plan_complexity": record.care_plan_complexity,
                "medication_count": record.medication_count
            }
        }
        
        # Get all diagnoses
        diagnoses = PatientDiagnosis.objects.filter(medical_record=record).order_by('-diagnosis_date')
        record_data["diagnoses"] = [{
            "diagnosis_code": d.diagnosis_code,
            "diagnosis_name": d.diagnosis_name,
            "diagnosis_date": d.diagnosis_date,
            "diagnosed_by": str(d.diagnosed_by) if d.diagnosed_by else None,
            "is_chronic": d.is_chronic,
            "is_active": d.is_active,
            "severity_rating": d.severity_rating,
            "notes": d.notes
        } for d in diagnoses]
        
        # Get all treatments
        treatments = PatientTreatment.objects.filter(medical_record=record).order_by('-start_date')
        record_data["treatments"] = [{
            "treatment_type": t.treatment_type,
            "treatment_name": t.treatment_name,
            "treatment_code": t.treatment_code,
            "prescribed_by": str(t.prescribed_by) if t.prescribed_by else None,
            "start_date": t.start_date,
            "end_date": t.end_date,
            "is_active": t.is_active,
            "dosage": t.dosage,
            "frequency": t.frequency,
            "notes": t.notes
        } for t in treatments]
        
        # Get all doctor interactions
        interactions = DoctorInteraction.objects.filter(medical_record=record).order_by('-interaction_date')
        record_data["doctor_interactions"] = [{
            "doctor": str(i.doctor) if i.doctor else None,
            "interaction_date": i.interaction_date,
            "interaction_type": i.interaction_type,
            "patient_rating": i.patient_rating,
            "doctor_notes": i.doctor_notes,
            "communication_issues": i.communication_issues,
            "communication_notes": i.communication_notes
        } for i in interactions]
        
        return record_data
        
    except MedicalRecord.DoesNotExist:
        return {"error": f"No medical record found with HPN: {hpn}"}
    except Exception as e:
        return {"error": f"Error retrieving medical record: {str(e)}"}

def list_all_hpns():
    """List all HPNs in the system"""
    return [record.hpn for record in MedicalRecord.objects.all()]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_medical_records_by_hpn.py [HPN]")
        print("Or use: python get_medical_records_by_hpn.py --list to show all HPNs")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        print("Available HPN numbers:")
        hpns = list_all_hpns()
        for hpn in hpns:
            print(f" - {hpn}")
    else:
        hpn = sys.argv[1]
        result = get_medical_record_by_hpn(hpn)
        pprint(result) 