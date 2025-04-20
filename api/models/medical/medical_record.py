# api/models/medical/medical_record.py

from django.db import models
from django.utils import timezone
from ..user.custom_user import CustomUser

class MedicalRecord(models.Model):
    # One-to-one relationship with User
    user = models.OneToOneField(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_record'
    )
    # We use the HPN as the central identifier
    hpn = models.CharField(max_length=30, unique=True)
    is_anonymous = models.BooleanField(default=False)  # Flag for anonymization

    # Medical details
    blood_type = models.CharField(
        max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        null=True, blank=True
    )
    allergies = models.TextField(null=True, blank=True)
    chronic_conditions = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, null=True, blank=True)
    is_high_risk = models.BooleanField(default=False)
    last_visit_date = models.DateTimeField(null=True, blank=True)
    
    # New fields for ML doctor assignment
    comorbidity_count = models.IntegerField(default=0)
    hospitalization_count = models.IntegerField(default=0)
    last_hospitalization_date = models.DateTimeField(null=True, blank=True)
    care_plan_complexity = models.FloatField(default=0.0)  # 0-10 scale
    medication_count = models.IntegerField(default=0)

    def anonymize_record(self):
        """Mark the record as anonymous and disassociate it from the user."""
        self.is_anonymous = True
        self.user = None
        self.save()
        
    def update_complexity_metrics(self):
        """Update complexity metrics based on related records"""
        # Update comorbidity count
        self.comorbidity_count = self.diagnoses.filter(is_active=True).count()
        
        # Update medication count
        self.medication_count = self.treatments.filter(
            treatment_type='medication', 
            is_active=True
        ).count()
        
        # Calculate care plan complexity (0-10 scale)
        active_treatments = self.treatments.filter(is_active=True).count()
        active_diagnoses = self.diagnoses.filter(is_active=True).count()
        doctor_count = self.doctor_interactions.values('doctor').distinct().count()
        
        # Simple formula for care plan complexity
        self.care_plan_complexity = min(10.0, (
            (active_treatments * 0.5) + 
            (active_diagnoses * 1.0) + 
            (doctor_count * 0.5)
        ))
        
        self.save()

    def __str__(self):
        return f"Medical Record for HPN: {self.hpn}"


class PatientDiagnosis(models.Model):
    """Stores patient diagnosis information with ICD-10 codes"""
    medical_record = models.ForeignKey(
        MedicalRecord, 
        on_delete=models.CASCADE,
        related_name='diagnoses'
    )
    diagnosis_code = models.CharField(max_length=10)  # ICD-10 code
    diagnosis_name = models.CharField(max_length=255)
    diagnosis_date = models.DateTimeField()
    diagnosed_by = models.ForeignKey(
        'api.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='diagnoses_made'
    )
    is_chronic = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    severity_rating = models.IntegerField(default=1)  # 1-5 scale
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.diagnosis_code}: {self.diagnosis_name} ({self.medical_record.hpn})"


class PatientTreatment(models.Model):
    """Stores patient treatment information"""
    TREATMENT_TYPES = [
        ('medication', 'Medication'),
        ('procedure', 'Procedure'),
        ('therapy', 'Therapy'),
        ('surgery', 'Surgery'),
        ('other', 'Other')
    ]
    
    medical_record = models.ForeignKey(
        MedicalRecord, 
        on_delete=models.CASCADE,
        related_name='treatments'
    )
    treatment_type = models.CharField(max_length=20, choices=TREATMENT_TYPES)
    treatment_name = models.CharField(max_length=255)
    treatment_code = models.CharField(max_length=20, blank=True, null=True)
    prescribed_by = models.ForeignKey(
        'api.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='treatments_prescribed'
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    dosage = models.CharField(max_length=100, blank=True, null=True)  # For medications
    frequency = models.CharField(max_length=100, blank=True, null=True)  # For medications
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.treatment_type}: {self.treatment_name} ({self.medical_record.hpn})"


class DoctorInteraction(models.Model):
    """Stores patient-doctor interaction history"""
    INTERACTION_TYPES = [
        ('appointment', 'Appointment'),
        ('consultation', 'Consultation'),
        ('procedure', 'Procedure'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
        ('other', 'Other')
    ]
    
    medical_record = models.ForeignKey(
        MedicalRecord, 
        on_delete=models.CASCADE,
        related_name='doctor_interactions'
    )
    doctor = models.ForeignKey(
        'api.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='patient_interactions'
    )
    interaction_date = models.DateTimeField()
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    patient_rating = models.IntegerField(null=True, blank=True)  # 1-5 scale
    doctor_notes = models.TextField(blank=True, null=True)
    communication_issues = models.BooleanField(default=False)
    communication_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.interaction_type} with {self.doctor} on {self.interaction_date.strftime('%Y-%m-%d')}"