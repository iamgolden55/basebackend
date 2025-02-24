# api/models/medical/medical_record.py

from django.db import models
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

    def anonymize_record(self):
        """Mark the record as anonymous and disassociate it from the user."""
        self.is_anonymous = True
        self.user = None
        self.save()

    def __str__(self):
        return f"Medical Record for HPN: {self.hpn}"