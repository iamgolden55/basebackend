# api/models/medical/vital_signs.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from ..base import TimestampedModel
from .medical_record import MedicalRecord


class VitalSign(TimestampedModel):
    """
    Model for tracking patient vital signs over time
    """
    # Relationship to Medical Record
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='vital_signs',
        help_text="Medical record this vital sign belongs to"
    )
    
    # Recording Context
    recorded_at = models.DateTimeField(
        help_text="Date and time when vitals were recorded"
    )
    recorded_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_vital_signs',
        help_text="Healthcare provider who recorded these vitals"
    )
    location = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Location where vitals were recorded (e.g., 'ER', 'Home', 'Ward 4')"
    )
    context = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Context of measurement (e.g., 'Routine checkup', 'Post-surgery')"
    )
    
    # Blood Pressure
    systolic_bp = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(300)],
        help_text="Systolic blood pressure in mmHg"
    )
    diastolic_bp = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(200)],
        help_text="Diastolic blood pressure in mmHg"
    )
    
    # Heart Rate & Oxygen
    heart_rate = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(250)],
        help_text="Heart rate in beats per minute"
    )
    respiratory_rate = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(4), MaxValueValidator(60)],
        help_text="Respiratory rate in breaths per minute"
    )
    oxygen_saturation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(100)],
        help_text="Blood oxygen saturation in percentage"
    )
    
    # Temperature
    temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Body temperature"
    )
    temperature_unit = models.CharField(
        max_length=1,
        choices=[('C', 'Celsius'), ('F', 'Fahrenheit')],
        default='C',
        help_text="Temperature unit"
    )
    
    # Weight and BMI
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Patient weight"
    )
    weight_unit = models.CharField(
        max_length=2,
        choices=[('kg', 'Kilograms'), ('lb', 'Pounds')],
        default='kg',
        help_text="Weight unit"
    )
    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Patient height"
    )
    height_unit = models.CharField(
        max_length=2,
        choices=[('cm', 'Centimeters'), ('in', 'Inches')],
        default='cm',
        help_text="Height unit"
    )
    bmi = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Body Mass Index (calculated field)"
    )
    
    # Blood Glucose
    blood_glucose = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Blood glucose level"
    )
    glucose_unit = models.CharField(
        max_length=10,
        choices=[
            ('mg/dL', 'mg/dL'),
            ('mmol/L', 'mmol/L')
        ],
        default='mg/dL',
        help_text="Blood glucose unit of measurement"
    )
    glucose_timing = models.CharField(
        max_length=20,
        choices=[
            ('fasting', 'Fasting'),
            ('random', 'Random'),
            ('post_meal', 'Post-meal'),
            ('pre_meal', 'Pre-meal'),
            ('bedtime', 'Bedtime')
        ],
        null=True,
        blank=True,
        help_text="When glucose was measured relative to meals"
    )
    
    # Pain Scale
    pain_scale = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Pain scale from 0-10"
    )
    
    # Clinical Assessment
    is_abnormal = models.BooleanField(
        default=False,
        help_text="Whether any vitals are outside normal range"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about these vital signs"
    )
    
    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['medical_record', 'recorded_at']),
            models.Index(fields=['is_abnormal']),
        ]
    
    def __str__(self):
        return f"Vitals for {self.medical_record.hpn} at {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Calculate BMI if height and weight are provided
        if self.height and self.weight and self.height_unit and self.weight_unit:
            # Convert to standard units if needed (meters and kilograms)
            height_m = self.height / 100 if self.height_unit == 'cm' else self.height * 0.0254
            weight_kg = self.weight if self.weight_unit == 'kg' else self.weight * 0.453592
            
            # BMI formula: weight(kg) / (height(m) * height(m))
            if height_m > 0:
                self.bmi = round(weight_kg / (height_m * height_m), 2)
        
        # Determine if any vitals are abnormal
        self.is_abnormal = self._check_abnormal_values()
        
        super().save(*args, **kwargs)
    
    def _check_abnormal_values(self):
        """Check if any vital signs are outside normal ranges"""
        # Blood pressure
        if (self.systolic_bp and (self.systolic_bp < 90 or self.systolic_bp > 140)) or \
           (self.diastolic_bp and (self.diastolic_bp < 60 or self.diastolic_bp > 90)):
            return True
        
        # Heart rate
        if self.heart_rate and (self.heart_rate < 60 or self.heart_rate > 100):
            return True
        
        # Respiratory rate
        if self.respiratory_rate and (self.respiratory_rate < 12 or self.respiratory_rate > 20):
            return True
        
        # Oxygen saturation
        if self.oxygen_saturation and self.oxygen_saturation < 95:
            return True
        
        # Temperature (Celsius)
        if self.temperature:
            if self.temperature_unit == 'C' and (self.temperature < 36.1 or self.temperature > 37.8):
                return True
            elif self.temperature_unit == 'F' and (self.temperature < 97 or self.temperature > 100):
                return True
        
        # Blood glucose (mg/dL)
        if self.blood_glucose:
            if self.glucose_unit == 'mg/dL':
                if self.glucose_timing == 'fasting' and (self.blood_glucose < 70 or self.blood_glucose > 100):
                    return True
                elif self.glucose_timing and self.glucose_timing != 'fasting' and self.blood_glucose > 140:
                    return True
            elif self.glucose_unit == 'mmol/L':
                if self.glucose_timing == 'fasting' and (self.blood_glucose < 3.9 or self.blood_glucose > 5.6):
                    return True
                elif self.glucose_timing and self.glucose_timing != 'fasting' and self.blood_glucose > 7.8:
                    return True
        
        return False
    
    @property
    def blood_pressure(self):
        """Return formatted blood pressure string"""
        if self.systolic_bp and self.diastolic_bp:
            return f"{self.systolic_bp}/{self.diastolic_bp} mmHg"
        return None
    
    @property
    def formatted_temperature(self):
        """Return formatted temperature with unit"""
        if self.temperature:
            return f"{self.temperature}°{self.temperature_unit}"
        return None
    
    @property
    def formatted_weight(self):
        """Return formatted weight with unit"""
        if self.weight:
            return f"{self.weight} {self.weight_unit}"
        return None
    
    @property
    def formatted_height(self):
        """Return formatted height with unit"""
        if self.height:
            return f"{self.height} {self.height_unit}"
        return None
    
    @property
    def formatted_glucose(self):
        """Return formatted glucose with unit and timing"""
        if self.blood_glucose:
            timing = f" ({self.get_glucose_timing_display()})" if self.glucose_timing else ""
            return f"{self.blood_glucose} {self.glucose_unit}{timing}"
        return None
    
    def get_summary(self):
        """Return a dictionary summary of vital signs"""
        return {
            'date': self.recorded_at,
            'blood_pressure': self.blood_pressure,
            'heart_rate': f"{self.heart_rate} bpm" if self.heart_rate else None,
            'respiratory_rate': f"{self.respiratory_rate} bpm" if self.respiratory_rate else None,
            'temperature': self.formatted_temperature,
            'oxygen': f"{self.oxygen_saturation}%" if self.oxygen_saturation else None,
            'weight': self.formatted_weight,
            'height': self.formatted_height,
            'bmi': self.bmi,
            'glucose': self.formatted_glucose,
            'pain': self.pain_scale,
            'is_abnormal': self.is_abnormal,
            'location': self.location,
            'context': self.context
        } 