# api/models/medical/fertility_tracking.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from ..base import TimestampedModel
from .womens_health_profile import WomensHealthProfile


class FertilityTracking(TimestampedModel):
    """
    Model for tracking daily fertility signs, ovulation data, and symptoms
    for women trying to conceive or monitoring fertility
    """
    # Relationship
    womens_health_profile = models.ForeignKey(
        WomensHealthProfile,
        on_delete=models.CASCADE,
        related_name='fertility_tracking_entries',
        help_text="Women's health profile this fertility tracking belongs to"
    )
    
    # Date and Cycle Information
    date = models.DateField(
        help_text="Date of this fertility tracking entry"
    )
    
    cycle_day = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Day of menstrual cycle (1-based, day 1 = first day of period)"
    )
    
    # Basal Body Temperature (BBT)
    basal_body_temperature = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Basal body temperature in Celsius"
    )
    
    bbt_time_taken = models.TimeField(
        null=True,
        blank=True,
        help_text="Time when BBT was measured"
    )
    
    bbt_method = models.CharField(
        max_length=20,
        choices=[
            ('oral', 'Oral'),
            ('vaginal', 'Vaginal'),
            ('rectal', 'Rectal')
        ],
        null=True,
        blank=True,
        help_text="Method used to measure BBT"
    )
    
    bbt_disrupted = models.BooleanField(
        default=False,
        help_text="Whether BBT reading was disrupted (poor sleep, illness, etc.)"
    )
    
    bbt_disruption_reason = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Reason for BBT disruption"
    )
    
    # Cervical Mucus
    CERVICAL_MUCUS_CHOICES = [
        ('dry', 'Dry/None'),
        ('sticky', 'Sticky/Tacky'),
        ('creamy', 'Creamy/Lotion-like'),
        ('watery', 'Watery'),
        ('egg_white', 'Egg White/Stretchy'),
        ('spotting', 'Spotting/Blood'),
        ('unusual', 'Unusual')
    ]
    
    cervical_mucus_type = models.CharField(
        max_length=15,
        choices=CERVICAL_MUCUS_CHOICES,
        null=True,
        blank=True,
        help_text="Type of cervical mucus observed"
    )
    
    cervical_mucus_amount = models.CharField(
        max_length=15,
        choices=[
            ('none', 'None'),
            ('light', 'Light'),
            ('moderate', 'Moderate'),
            ('heavy', 'Heavy')
        ],
        null=True,
        blank=True,
        help_text="Amount of cervical mucus"
    )
    
    cervical_mucus_stretchy = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether cervical mucus is stretchy/elastic"
    )
    
    cervical_mucus_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about cervical mucus"
    )
    
    # Cervical Position (for advanced tracking)
    cervical_position_height = models.CharField(
        max_length=15,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High')
        ],
        null=True,
        blank=True,
        help_text="Height of cervical position"
    )
    
    cervical_position_firmness = models.CharField(
        max_length=15,
        choices=[
            ('soft', 'Soft'),
            ('medium', 'Medium'),
            ('firm', 'Firm')
        ],
        null=True,
        blank=True,
        help_text="Firmness of cervix"
    )
    
    cervical_position_opening = models.CharField(
        max_length=15,
        choices=[
            ('closed', 'Closed'),
            ('slightly_open', 'Slightly Open'),
            ('open', 'Open')
        ],
        null=True,
        blank=True,
        help_text="Opening of cervix"
    )
    
    # Ovulation Tests
    ovulation_test_taken = models.BooleanField(
        default=False,
        help_text="Whether an ovulation test was taken"
    )
    
    OVULATION_TEST_RESULT_CHOICES = [
        ('negative', 'Negative'),
        ('positive', 'Positive'),
        ('almost_positive', 'Almost Positive'),
        ('unclear', 'Unclear/Inconclusive'),
        ('error', 'Test Error')
    ]
    
    ovulation_test_result = models.CharField(
        max_length=20,
        choices=OVULATION_TEST_RESULT_CHOICES,
        null=True,
        blank=True,
        help_text="Result of ovulation test"
    )
    
    ovulation_test_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time when ovulation test was taken"
    )
    
    ovulation_test_brand = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Brand of ovulation test used"
    )
    
    # LH (Luteinizing Hormone) levels if using digital tests
    lh_level = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="LH level if using quantitative test"
    )
    
    # Pregnancy Tests
    pregnancy_test_taken = models.BooleanField(
        default=False,
        help_text="Whether a pregnancy test was taken"
    )
    
    PREGNANCY_TEST_RESULT_CHOICES = [
        ('negative', 'Negative'),
        ('positive', 'Positive'),
        ('faint_positive', 'Faint Positive'),
        ('unclear', 'Unclear/Inconclusive'),
        ('error', 'Test Error')
    ]
    
    pregnancy_test_result = models.CharField(
        max_length=20,
        choices=PREGNANCY_TEST_RESULT_CHOICES,
        null=True,
        blank=True,
        help_text="Result of pregnancy test"
    )
    
    pregnancy_test_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time when pregnancy test was taken"
    )
    
    pregnancy_test_brand = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Brand of pregnancy test used"
    )
    
    # Sexual Activity
    intercourse = models.BooleanField(
        default=False,
        help_text="Sexual intercourse occurred"
    )
    
    protected_intercourse = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether protection was used during intercourse"
    )
    
    intercourse_times = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Number of times intercourse occurred"
    )
    
    trying_to_conceive = models.BooleanField(
        default=False,
        help_text="Actively trying to conceive"
    )
    
    # Physical Symptoms
    symptoms = models.JSONField(
        default=list,
        blank=True,
        help_text="List of physical symptoms experienced"
    )
    
    # Common fertility symptoms
    ovulation_pain = models.BooleanField(
        default=False,
        help_text="Ovulation pain (mittelschmerz)"
    )
    
    ovulation_pain_side = models.CharField(
        max_length=10,
        choices=[
            ('left', 'Left'),
            ('right', 'Right'),
            ('both', 'Both'),
            ('center', 'Center')
        ],
        null=True,
        blank=True,
        help_text="Side where ovulation pain occurred"
    )
    
    breast_tenderness = models.BooleanField(
        default=False,
        help_text="Breast tenderness or sensitivity"
    )
    
    spotting = models.BooleanField(
        default=False,
        help_text="Spotting or light bleeding"
    )
    
    spotting_color = models.CharField(
        max_length=15,
        choices=[
            ('brown', 'Brown'),
            ('pink', 'Pink'),
            ('red', 'Red'),
            ('other', 'Other')
        ],
        null=True,
        blank=True,
        help_text="Color of spotting"
    )
    
    cramps = models.BooleanField(
        default=False,
        help_text="Cramping or abdominal pain"
    )
    
    headache = models.BooleanField(
        default=False,
        help_text="Headache"
    )
    
    nausea = models.BooleanField(
        default=False,
        help_text="Nausea"
    )
    
    fatigue = models.BooleanField(
        default=False,
        help_text="Unusual fatigue or tiredness"
    )
    
    mood_changes = models.BooleanField(
        default=False,
        help_text="Mood changes or emotional symptoms"
    )
    
    increased_appetite = models.BooleanField(
        default=False,
        help_text="Increased appetite or food cravings"
    )
    
    decreased_appetite = models.BooleanField(
        default=False,
        help_text="Decreased appetite"
    )
    
    # Sleep and Energy
    sleep_quality = models.CharField(
        max_length=15,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('very_poor', 'Very Poor')
        ],
        null=True,
        blank=True,
        help_text="Quality of sleep"
    )
    
    sleep_hours = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Hours of sleep"
    )
    
    energy_level = models.CharField(
        max_length=15,
        choices=[
            ('very_low', 'Very Low'),
            ('low', 'Low'),
            ('normal', 'Normal'),
            ('high', 'High'),
            ('very_high', 'Very High')
        ],
        null=True,
        blank=True,
        help_text="Energy level for the day"
    )
    
    # Lifestyle Factors
    stress_level = models.CharField(
        max_length=15,
        choices=[
            ('very_low', 'Very Low'),
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High'),
            ('very_high', 'Very High')
        ],
        null=True,
        blank=True,
        help_text="Stress level for the day"
    )
    
    exercise = models.BooleanField(
        default=False,
        help_text="Exercise or physical activity"
    )
    
    exercise_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Type of exercise performed"
    )
    
    exercise_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Exercise duration in minutes"
    )
    
    alcohol_consumption = models.BooleanField(
        default=False,
        help_text="Alcohol consumption"
    )
    
    caffeine_consumption = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of caffeinated drinks"
    )
    
    # Medications and Supplements
    medications = models.JSONField(
        default=list,
        blank=True,
        help_text="Medications taken today"
    )
    
    prenatal_vitamins = models.BooleanField(
        default=False,
        help_text="Prenatal vitamins taken"
    )
    
    folic_acid = models.BooleanField(
        default=False,
        help_text="Folic acid supplement taken"
    )
    
    other_supplements = models.JSONField(
        default=list,
        blank=True,
        help_text="Other supplements taken"
    )
    
    # Fertility Treatments
    fertility_treatment = models.BooleanField(
        default=False,
        help_text="Undergoing fertility treatment"
    )
    
    fertility_treatment_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Type of fertility treatment"
    )
    
    fertility_medications = models.JSONField(
        default=list,
        blank=True,
        help_text="Fertility medications taken"
    )
    
    # Notes and Custom Tracking
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes for this day"
    )
    
    custom_symptoms = models.JSONField(
        default=list,
        blank=True,
        help_text="Custom symptoms or observations"
    )
    
    # Data Quality
    data_completeness_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
        help_text="Percentage of tracking data completed for this day"
    )
    
    # Metadata
    entered_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='fertility_tracking_entries',
        help_text="User who entered this fertility data"
    )
    
    entry_method = models.CharField(
        max_length=20,
        choices=[
            ('manual', 'Manual Entry'),
            ('app', 'Mobile App'),
            ('import', 'Data Import'),
            ('device', 'Connected Device')
        ],
        default='manual',
        help_text="Method used to enter this data"
    )
    
    class Meta:
        verbose_name = "Fertility Tracking Entry"
        verbose_name_plural = "Fertility Tracking Entries"
        indexes = [
            models.Index(fields=['womens_health_profile', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['cycle_day']),
            models.Index(fields=['ovulation_test_result']),
            models.Index(fields=['basal_body_temperature']),
        ]
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['womens_health_profile', 'date'],
                name='unique_fertility_tracking_per_date'
            )
        ]
    
    def __str__(self):
        user_name = self.womens_health_profile.user.get_full_name() or self.womens_health_profile.user.username
        return f"Fertility Tracking - {self.date} - {user_name}"
    
    def save(self, *args, **kwargs):
        # Calculate data completeness
        self.calculate_data_completeness()
        super().save(*args, **kwargs)
    
    def calculate_data_completeness(self):
        """Calculate what percentage of fertility tracking data was completed"""
        total_fields = 0
        completed_fields = 0
        
        # Core tracking fields
        core_fields = [
            'basal_body_temperature', 'cervical_mucus_type', 
            'ovulation_test_taken', 'intercourse'
        ]
        
        for field in core_fields:
            total_fields += 1
            field_value = getattr(self, field)
            if field_value is not None and field_value != False:
                completed_fields += 1
        
        # Optional but valuable fields
        optional_fields = [
            'symptoms', 'stress_level', 'sleep_quality', 'exercise'
        ]
        
        for field in optional_fields:
            total_fields += 1
            field_value = getattr(self, field)
            if field_value is not None and field_value not in [False, [], '']:
                completed_fields += 1
        
        self.data_completeness_score = int((float(completed_fields) / float(total_fields)) * 100) if total_fields > 0 else 0
    
    @property
    def is_potential_ovulation_day(self):
        """Check if this day shows signs of ovulation"""
        ovulation_indicators = []
        
        # BBT dip or rise
        if self.basal_body_temperature:
            # Would need previous days' data to determine temperature shift
            # This is a simplified check
            ovulation_indicators.append('bbt_data')
        
        # Fertile cervical mucus
        if self.cervical_mucus_type in ['watery', 'egg_white']:
            ovulation_indicators.append('fertile_mucus')
        
        # Positive ovulation test
        if self.ovulation_test_result == 'positive':
            ovulation_indicators.append('positive_opk')
        
        # Ovulation pain
        if self.ovulation_pain:
            ovulation_indicators.append('ovulation_pain')
        
        # High cervical position
        if self.cervical_position_height == 'high':
            ovulation_indicators.append('high_cervix')
        
        return len(ovulation_indicators) >= 2
    
    @property
    def fertility_score(self):
        """Calculate a fertility score for this day (0-10)"""
        score = 0
        
        # Cervical mucus scoring
        mucus_scores = {
            'dry': 0,
            'sticky': 1,
            'creamy': 2,
            'watery': 3,
            'egg_white': 4
        }
        if self.cervical_mucus_type in mucus_scores:
            score += mucus_scores[self.cervical_mucus_type]
        
        # Ovulation test
        if self.ovulation_test_result == 'positive':
            score += 3
        elif self.ovulation_test_result == 'almost_positive':
            score += 2
        
        # Ovulation pain
        if self.ovulation_pain:
            score += 1
        
        # Cervical position
        if self.cervical_position_height == 'high':
            score += 1
        if self.cervical_position_firmness == 'soft':
            score += 1
        
        return min(score, 10)  # Cap at 10
    
    def get_fertile_window_status(self):
        """Determine if this day is in the fertile window"""
        fertility_score = self.fertility_score
        
        if fertility_score >= 7:
            return {'status': 'peak_fertility', 'message': 'Peak fertility day'}
        elif fertility_score >= 4:
            return {'status': 'high_fertility', 'message': 'High fertility'}
        elif fertility_score >= 2:
            return {'status': 'moderate_fertility', 'message': 'Moderate fertility'}
        else:
            return {'status': 'low_fertility', 'message': 'Low fertility'}
    
    def get_summary(self):
        """Return fertility tracking summary for API responses"""
        return {
            'date': self.date.isoformat(),
            'cycle_day': self.cycle_day,
            'bbt': float(self.basal_body_temperature) if self.basal_body_temperature else None,
            'cervical_mucus': self.get_cervical_mucus_type_display() if self.cervical_mucus_type else None,
            'ovulation_test': self.get_ovulation_test_result_display() if self.ovulation_test_result else None,
            'intercourse': self.intercourse,
            'fertility_score': self.fertility_score,
            'fertile_window_status': self.get_fertile_window_status(),
            'potential_ovulation': self.is_potential_ovulation_day,
            'symptoms': self.symptoms,
            'data_completeness': f"{self.data_completeness_score}%"
        }