# api/models/medical/medical_history_extended.py

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class MedicalHistory(models.Model):
    """
    Extended medical history model for agent functionality.
    This complements the existing MedicalRecord model.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='extended_medical_history'
    )
    
    # JSON fields for flexible data storage
    medical_conditions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of current medical conditions"
    )
    
    medications = models.JSONField(
        default=list,
        blank=True,
        help_text="List of current medications with dosage and frequency"
    )
    
    allergies = models.JSONField(
        default=list,
        blank=True,
        help_text="List of known allergies"
    )
    
    family_history = models.JSONField(
        default=dict,
        blank=True,
        help_text="Family medical history by condition"
    )
    
    surgical_history = models.JSONField(
        default=list,
        blank=True,
        help_text="List of previous surgeries and procedures"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Extended Medical History"
        verbose_name_plural = "Extended Medical Histories"
    
    def __str__(self):
        return f"Medical History for {self.user.email}"