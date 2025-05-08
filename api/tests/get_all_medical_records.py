#!/usr/bin/env python
import os
import sys
import django
import json
from datetime import datetime

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

# Import models after setting up Django
from api.models.medical.medical_record import MedicalRecord, PatientDiagnosis, PatientTreatment, DoctorInteraction

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def get_all_medical_records(summary_only=False):
    """Retrieve all medical records in the system"""
    all_records = []
    
    for record in MedicalRecord.objects.all():
        if summary_only:
            # Just the basic info
            record_data = {
                "hpn": record.hpn,
                "patient_name": f"{record.user.first_name} {record.user.last_name}" if record.user else "Anonymous",
                "blood_type": record.blood_type,
                "is_high_risk": record.is_high_risk,
                "diagnoses_count": record.diagnoses.count(),
                "active_treatments_count": record.treatments.filter(is_active=True).count(),
            }
        else:
            # Full comprehensive details
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
            
            # Include diagnoses if not summary
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
            
            # Include treatments if not summary
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
            
            # Include doctor interactions if not summary
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
        
        all_records.append(record_data)
    
    return all_records

if __name__ == "__main__":
    # Check for command line options
    summary_only = "--summary" in sys.argv
    output_file = None
    
    # Check if output file is specified
    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i+1 < len(sys.argv):
            output_file = sys.argv[i+1]
    
    # Get the records
    records = get_all_medical_records(summary_only=summary_only)
    
    # Count total records
    print(f"Total medical records: {len(records)}")
    
    # Output to file or print
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(records, f, cls=DateTimeEncoder, indent=2)
        print(f"Results written to {output_file}")
    else:
        for record in records:
            hpn = record['hpn']
            name = record['patient_name']
            print(f"HPN: {hpn} - Patient: {name}")
            
        print("\nFor complete details, use one of the following:")
        print("1. Specify an output file: python get_all_medical_records.py --output records.json")
        print("2. Get summary only: python get_all_medical_records.py --summary")
        print("3. For individual records: python get_medical_records_by_hpn.py [HPN]") 