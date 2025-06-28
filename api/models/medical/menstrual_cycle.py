# api/models/medical/menstrual_cycle.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from ..base import TimestampedModel
from .womens_health_profile import WomensHealthProfile


class MenstrualCycle(TimestampedModel):
    """
    Model for tracking individual menstrual cycles and related data
    """
    # Relationship
    womens_health_profile = models.ForeignKey(
        WomensHealthProfile,
        on_delete=models.CASCADE,
        related_name='menstrual_cycles',
        help_text="Women's health profile this cycle belongs to"
    )
    
    # Cycle Information
    cycle_start_date = models.DateField(
        help_text="First day of menstrual period"
    )
    
    cycle_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Last day before next cycle starts (auto-calculated)"
    )
    
    period_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Last day of menstrual bleeding"
    )
    
    cycle_length = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(15), MaxValueValidator(50)],
        help_text="Total cycle length in days (15-50)"
    )
    
    period_length = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(15)],
        help_text="Period duration in days (1-15)"
    )
    
    # Flow Characteristics
    FLOW_INTENSITY_CHOICES = [
        ('spotting', 'Spotting'),
        ('light', 'Light'),
        ('medium', 'Medium'),
        ('heavy', 'Heavy'),
        ('very_heavy', 'Very Heavy')
    ]
    
    flow_intensity = models.CharField(
        max_length=20,
        choices=FLOW_INTENSITY_CHOICES,
        null=True,
        blank=True,
        help_text="Overall flow intensity for this cycle"
    )
    
    # Ovulation Information
    ovulation_date = models.DateField(
        null=True,
        blank=True,
        help_text="Confirmed or estimated ovulation date"
    )
    
    ovulation_confirmed = models.BooleanField(
        default=False,
        help_text="Whether ovulation was confirmed (vs estimated)"
    )
    
    OVULATION_METHOD_CHOICES = [
        ('temperature', 'Basal Body Temperature'),
        ('mucus', 'Cervical Mucus'),
        ('ovulation_test', 'Ovulation Test'),
        ('ultrasound', 'Ultrasound'),
        ('calculated', 'Calculated Estimate'),
        ('app_prediction', 'App Prediction'),
        ('multiple', 'Multiple Methods')
    ]
    
    ovulation_detection_method = models.CharField(
        max_length=20,
        choices=OVULATION_METHOD_CHOICES,
        null=True,
        blank=True,
        help_text="Method used to detect/estimate ovulation"
    )
    
    # Cycle Quality and Regularity
    is_regular = models.BooleanField(
        default=True,
        help_text="Whether this cycle was regular for the user"
    )
    
    cycle_quality_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True,
        blank=True,
        help_text="Subjective cycle quality rating (1-10)"
    )
    
    # Pregnancy and Conception
    pregnancy_test_taken = models.BooleanField(
        default=False,
        help_text="Whether a pregnancy test was taken this cycle"
    )
    
    pregnancy_test_result = models.CharField(
        max_length=20,
        choices=[
            ('positive', 'Positive'),
            ('negative', 'Negative'),
            ('unclear', 'Unclear/Faint'),
            ('not_taken', 'Not Taken')
        ],
        default='not_taken',
        help_text="Pregnancy test result"
    )
    
    pregnancy_test_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date pregnancy test was taken"
    )
    
    conception_attempt = models.BooleanField(
        default=False,
        help_text="Whether actively trying to conceive this cycle"
    )
    
    # Medications and Supplements
    medications_taken = models.JSONField(
        default=list,
        blank=True,
        help_text="List of medications taken during this cycle"
    )
    
    supplements_taken = models.JSONField(
        default=list,
        blank=True,
        help_text="List of supplements taken during this cycle"
    )
    
    hormonal_contraception = models.BooleanField(
        default=False,
        help_text="Whether on hormonal contraception during this cycle"
    )
    
    # Lifestyle Factors
    stress_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High'),
            ('severe', 'Severe')
        ],
        null=True,
        blank=True,
        help_text="Average stress level during this cycle"
    )
    
    exercise_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('several_times_week', 'Several times per week'),
            ('weekly', 'Weekly'),
            ('rarely', 'Rarely'),
            ('none', 'None')
        ],
        null=True,
        blank=True,
        help_text="Exercise frequency during this cycle"
    )
    
    travel_during_cycle = models.BooleanField(
        default=False,
        help_text="Whether traveled during this cycle"
    )
    
    illness_during_cycle = models.BooleanField(
        default=False,
        help_text="Whether experienced illness during this cycle"
    )
    
    # Data Quality and Completeness
    data_completeness_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
        help_text="Percentage of cycle data that was tracked (0-100)"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this cycle"
    )
    
    # Metadata
    is_current_cycle = models.BooleanField(
        default=False,
        help_text="Whether this is the current ongoing cycle"
    )
    
    predicted_cycle = models.BooleanField(
        default=False,
        help_text="Whether this cycle data includes predictions"
    )
    
    class Meta:
        verbose_name = "Menstrual Cycle"
        verbose_name_plural = "Menstrual Cycles"
        indexes = [
            models.Index(fields=['womens_health_profile', 'cycle_start_date']),
            models.Index(fields=['cycle_start_date']),
            models.Index(fields=['ovulation_date']),
            models.Index(fields=['is_current_cycle']),
        ]
        ordering = ['-cycle_start_date']
    
    def __str__(self):
        return f"Cycle starting {self.cycle_start_date} - {self.womens_health_profile.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # Calculate data completeness
        self.calculate_data_completeness()
        
        # Calculate cycle length if end date is provided
        if self.cycle_end_date and not self.cycle_length:
            self.cycle_length = (self.cycle_end_date - self.cycle_start_date).days + 1
        
        # Calculate period length if end date is provided
        if self.period_end_date and not self.period_length:
            self.period_length = (self.period_end_date - self.cycle_start_date).days + 1
        
        # Ensure only one current cycle per profile
        if self.is_current_cycle:
            MenstrualCycle.objects.filter(
                womens_health_profile=self.womens_health_profile,
                is_current_cycle=True
            ).exclude(id=self.id).update(is_current_cycle=False)
        
        super().save(*args, **kwargs)
    
    def calculate_data_completeness(self):
        """Calculate what percentage of cycle data has been tracked"""
        total_fields = 0
        completed_fields = 0
        
        # Core tracking fields
        core_fields = [
            'cycle_start_date', 'period_end_date', 'flow_intensity',
            'ovulation_date', 'cycle_quality_score'
        ]
        
        for field in core_fields:
            total_fields += 1
            if getattr(self, field):
                completed_fields += 1
        
        # Optional but valuable fields
        optional_fields = [
            'stress_level', 'exercise_frequency', 'pregnancy_test_taken'
        ]
        
        for field in optional_fields:
            total_fields += 1
            if getattr(self, field) not in [None, False, '']:
                completed_fields += 1
        
        self.data_completeness_score = int((float(completed_fields) / float(total_fields)) * 100) if total_fields > 0 else 0
    
    @property
    def cycle_day(self):
        """Current day of cycle (if this is current cycle)"""
        if not self.is_current_cycle:
            return None
        
        today = timezone.now().date()
        if today < self.cycle_start_date:
            return None
        
        return (today - self.cycle_start_date).days + 1
    
    @property
    def days_until_ovulation(self):
        """Days until estimated ovulation (if current cycle)"""
        if not self.is_current_cycle or not self.ovulation_date:
            return None
        
        today = timezone.now().date()
        if today > self.ovulation_date:
            return 0  # Ovulation has passed
        
        return (self.ovulation_date - today).days
    
    @property
    def is_in_fertile_window(self):
        """Check if currently in fertile window (5 days before + day of ovulation)"""
        if not self.is_current_cycle or not self.ovulation_date:
            return False
        
        today = timezone.now().date()
        fertile_start = self.ovulation_date - timezone.timedelta(days=5)
        fertile_end = self.ovulation_date
        
        return fertile_start <= today <= fertile_end
    
    @property
    def cycle_phase(self):
        """Determine current phase of cycle"""
        if not self.is_current_cycle:
            return None
        
        current_day = self.cycle_day
        if not current_day:
            return None
        
        # Menstrual phase (days 1-5 typically)
        if current_day <= (self.period_length or 5):
            return {
                'phase': 'menstrual',
                'display': 'Menstrual',
                'description': 'Menstrual bleeding period'
            }
        
        # Estimate ovulation day (typically 14 days before next cycle)
        estimated_cycle_length = self.womens_health_profile.average_cycle_length
        estimated_ovulation_day = estimated_cycle_length - 14
        
        # Follicular phase (after menstruation until ovulation)
        if current_day < estimated_ovulation_day - 2:
            return {
                'phase': 'follicular',
                'display': 'Follicular',
                'description': 'Pre-ovulation phase'
            }
        
        # Ovulation phase (around ovulation day)
        if estimated_ovulation_day - 2 <= current_day <= estimated_ovulation_day + 2:
            return {
                'phase': 'ovulation',
                'display': 'Ovulation',
                'description': 'Ovulation window'
            }
        
        # Luteal phase (after ovulation)
        return {
            'phase': 'luteal',
            'display': 'Luteal',
            'description': 'Post-ovulation phase'
        }
    
    def get_fertility_status(self):
        """Get fertility status for this cycle"""
        if not self.is_current_cycle:
            return {'status': 'not_current', 'message': 'Not current cycle'}
        
        if self.is_in_fertile_window:
            return {
                'status': 'fertile',
                'message': 'In fertile window',
                'days_until_ovulation': self.days_until_ovulation
            }
        
        if self.days_until_ovulation and self.days_until_ovulation > 0:
            return {
                'status': 'pre_fertile',
                'message': f'{self.days_until_ovulation} days until fertile window',
                'days_until_ovulation': self.days_until_ovulation
            }
        
        return {
            'status': 'post_fertile',
            'message': 'Past fertile window for this cycle',
            'days_until_ovulation': 0
        }
    
    def get_summary(self):
        """Return cycle summary for API responses"""
        return {
            'cycle_start': self.cycle_start_date.isoformat() if self.cycle_start_date else None,
            'cycle_length': self.cycle_length,
            'period_length': self.period_length,
            'flow_intensity': self.get_flow_intensity_display() if self.flow_intensity else None,
            'ovulation_date': self.ovulation_date.isoformat() if self.ovulation_date else None,
            'ovulation_confirmed': self.ovulation_confirmed,
            'is_current': self.is_current_cycle,
            'cycle_phase': self.cycle_phase,
            'fertility_status': self.get_fertility_status(),
            'data_completeness': f"{self.data_completeness_score}%",
            'cycle_quality': self.cycle_quality_score
        }