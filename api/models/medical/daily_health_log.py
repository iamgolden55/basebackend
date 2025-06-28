# api/models/medical/daily_health_log.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from ..base import TimestampedModel
from .womens_health_profile import WomensHealthProfile


class DailyHealthLog(TimestampedModel):
    """
    Model for tracking daily health and wellness data for women's health
    """
    # Relationship
    womens_health_profile = models.ForeignKey(
        WomensHealthProfile,
        on_delete=models.CASCADE,
        related_name='daily_health_logs',
        help_text="Women's health profile this daily log belongs to"
    )
    
    # Date
    date = models.DateField(
        help_text="Date of this health log entry"
    )
    
    # Physical Health Metrics
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weight in kilograms"
    )
    
    body_fat_percentage = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Body fat percentage"
    )
    
    muscle_mass_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Muscle mass in kilograms"
    )
    
    # Vital Signs
    systolic_bp = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(300)],
        help_text="Systolic blood pressure (mmHg)"
    )
    
    diastolic_bp = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(200)],
        help_text="Diastolic blood pressure (mmHg)"
    )
    
    heart_rate_bpm = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(220)],
        help_text="Heart rate in beats per minute"
    )
    
    resting_heart_rate = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(120)],
        help_text="Resting heart rate in beats per minute"
    )
    
    body_temperature = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Body temperature in Celsius"
    )
    
    # Sleep Tracking
    sleep_bedtime = models.TimeField(
        null=True,
        blank=True,
        help_text="Time went to bed"
    )
    
    sleep_wake_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time woke up"
    )
    
    sleep_duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total sleep duration in hours"
    )
    
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
        help_text="Subjective sleep quality rating"
    )
    
    sleep_interrupted = models.BooleanField(
        default=False,
        help_text="Whether sleep was interrupted"
    )
    
    sleep_interruption_count = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text="Number of times sleep was interrupted"
    )
    
    sleep_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about sleep"
    )
    
    # Nutrition and Hydration
    water_intake_liters = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Water intake in liters"
    )
    
    water_goal_met = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether daily water intake goal was met"
    )
    
    meals_count = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(15)],
        help_text="Number of meals/snacks consumed"
    )
    
    vegetables_servings = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text="Number of vegetable servings"
    )
    
    fruits_servings = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text="Number of fruit servings"
    )
    
    caffeine_intake_mg = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(2000)],
        help_text="Caffeine intake in milligrams"
    )
    
    alcohol_units = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Alcohol consumption in standard units"
    )
    
    # Exercise and Physical Activity
    exercise_performed = models.BooleanField(
        default=False,
        help_text="Whether exercise was performed"
    )
    
    exercise_duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(600)],
        help_text="Total exercise duration in minutes"
    )
    
    exercise_intensity = models.CharField(
        max_length=15,
        choices=[
            ('light', 'Light'),
            ('moderate', 'Moderate'),
            ('vigorous', 'Vigorous'),
            ('high', 'High Intensity')
        ],
        null=True,
        blank=True,
        help_text="Exercise intensity level"
    )
    
    exercise_types = models.JSONField(
        default=list,
        blank=True,
        help_text="Types of exercise performed"
    )
    
    steps_count = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100000)],
        help_text="Daily step count"
    )
    
    active_minutes = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1440)],
        help_text="Active minutes throughout the day"
    )
    
    calories_burned = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10000)],
        help_text="Estimated calories burned from exercise"
    )
    
    # Mental Health and Mood
    MOOD_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('neutral', 'Neutral'),
        ('low', 'Low'),
        ('poor', 'Poor'),
        ('anxious', 'Anxious'),
        ('stressed', 'Stressed'),
        ('depressed', 'Depressed')
    ]
    
    mood = models.CharField(
        max_length=15,
        choices=MOOD_CHOICES,
        null=True,
        blank=True,
        help_text="Overall mood for the day"
    )
    
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
    
    anxiety_level = models.CharField(
        max_length=15,
        choices=[
            ('none', 'None'),
            ('mild', 'Mild'),
            ('moderate', 'Moderate'),
            ('severe', 'Severe')
        ],
        null=True,
        blank=True,
        help_text="Anxiety level for the day"
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
    
    emotional_wellbeing_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Emotional wellbeing score (1-10)"
    )
    
    # Symptoms and Health Issues
    symptoms = models.JSONField(
        default=list,
        blank=True,
        help_text="List of symptoms experienced today"
    )
    
    pain_level = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Pain level (0-10 scale)"
    )
    
    pain_location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Location of pain if applicable"
    )
    
    headache = models.BooleanField(
        default=False,
        help_text="Experienced headache"
    )
    
    nausea = models.BooleanField(
        default=False,
        help_text="Experienced nausea"
    )
    
    dizziness = models.BooleanField(
        default=False,
        help_text="Experienced dizziness"
    )
    
    fatigue = models.BooleanField(
        default=False,
        help_text="Experienced unusual fatigue"
    )
    
    # Medications and Supplements
    medications_taken = models.JSONField(
        default=list,
        blank=True,
        help_text="Medications taken today"
    )
    
    supplements_taken = models.JSONField(
        default=list,
        blank=True,
        help_text="Supplements taken today"
    )
    
    prenatal_vitamin = models.BooleanField(
        default=False,
        help_text="Prenatal vitamin taken"
    )
    
    folic_acid = models.BooleanField(
        default=False,
        help_text="Folic acid supplement taken"
    )
    
    birth_control = models.BooleanField(
        default=False,
        help_text="Birth control medication taken"
    )
    
    missed_medications = models.JSONField(
        default=list,
        blank=True,
        help_text="List of medications that were missed"
    )
    
    # Women's Health Specific
    menstrual_flow = models.CharField(
        max_length=15,
        choices=[
            ('none', 'None'),
            ('spotting', 'Spotting'),
            ('light', 'Light'),
            ('medium', 'Medium'),
            ('heavy', 'Heavy'),
            ('very_heavy', 'Very Heavy')
        ],
        null=True,
        blank=True,
        help_text="Menstrual flow intensity"
    )
    
    menstrual_cramps = models.BooleanField(
        default=False,
        help_text="Experienced menstrual cramps"
    )
    
    cramp_severity = models.CharField(
        max_length=15,
        choices=[
            ('mild', 'Mild'),
            ('moderate', 'Moderate'),
            ('severe', 'Severe')
        ],
        null=True,
        blank=True,
        help_text="Severity of menstrual cramps"
    )
    
    breast_tenderness = models.BooleanField(
        default=False,
        help_text="Experienced breast tenderness"
    )
    
    pms_symptoms = models.JSONField(
        default=list,
        blank=True,
        help_text="PMS symptoms experienced"
    )
    
    vaginal_discharge = models.CharField(
        max_length=15,
        choices=[
            ('none', 'None'),
            ('normal', 'Normal'),
            ('unusual', 'Unusual')
        ],
        null=True,
        blank=True,
        help_text="Vaginal discharge status"
    )
    
    # Pregnancy-Related (if applicable)
    morning_sickness = models.BooleanField(
        default=False,
        help_text="Experienced morning sickness"
    )
    
    pregnancy_symptoms = models.JSONField(
        default=list,
        blank=True,
        help_text="Pregnancy-related symptoms"
    )
    
    prenatal_appointment = models.BooleanField(
        default=False,
        help_text="Had prenatal appointment today"
    )
    
    fetal_movement = models.BooleanField(
        null=True,
        blank=True,
        help_text="Felt fetal movement (if pregnant)"
    )
    
    fetal_movement_count = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Number of fetal movements felt"
    )
    
    # Environmental and Lifestyle Factors
    weather_affected_mood = models.BooleanField(
        default=False,
        help_text="Weather affected mood"
    )
    
    social_interactions = models.CharField(
        max_length=15,
        choices=[
            ('none', 'None'),
            ('minimal', 'Minimal'),
            ('moderate', 'Moderate'),
            ('high', 'High')
        ],
        null=True,
        blank=True,
        help_text="Level of social interactions"
    )
    
    work_stress = models.CharField(
        max_length=15,
        choices=[
            ('none', 'None'),
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High'),
            ('overwhelming', 'Overwhelming')
        ],
        null=True,
        blank=True,
        help_text="Work-related stress level"
    )
    
    # Goal Progress Tracking
    goal_progress = models.JSONField(
        default=dict,
        blank=True,
        help_text="Progress updates for health goals"
    )
    
    # Self-Care Activities
    self_care_activities = models.JSONField(
        default=list,
        blank=True,
        help_text="Self-care activities performed today"
    )
    
    meditation_minutes = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(300)],
        help_text="Minutes spent in meditation/mindfulness"
    )
    
    relaxation_activities = models.JSONField(
        default=list,
        blank=True,
        help_text="Relaxation activities performed"
    )
    
    # Notes and Reflections
    daily_notes = models.TextField(
        blank=True,
        null=True,
        help_text="General notes about the day"
    )
    
    gratitude_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Things grateful for today"
    )
    
    achievements = models.JSONField(
        default=list,
        blank=True,
        help_text="Daily achievements or wins"
    )
    
    challenges = models.JSONField(
        default=list,
        blank=True,
        help_text="Challenges faced today"
    )
    
    # Data Quality and Completeness
    data_completeness_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
        help_text="Percentage of daily health data completed"
    )
    
    manual_entry = models.BooleanField(
        default=True,
        help_text="Whether data was entered manually"
    )
    
    device_sync_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Data synced from wearable devices"
    )
    
    # Metadata
    entry_time = models.DateTimeField(
        auto_now_add=True,
        help_text="When this log entry was created"
    )
    
    last_modified_time = models.DateTimeField(
        auto_now=True,
        help_text="When this log entry was last modified"
    )
    
    entered_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='daily_health_logs',
        help_text="User who entered this health log"
    )
    
    class Meta:
        verbose_name = "Daily Health Log"
        verbose_name_plural = "Daily Health Logs"
        indexes = [
            models.Index(fields=['womens_health_profile', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['mood']),
            models.Index(fields=['exercise_performed']),
            models.Index(fields=['menstrual_flow']),
        ]
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['womens_health_profile', 'date'],
                name='unique_daily_health_log_per_date'
            )
        ]
    
    def __str__(self):
        user_name = self.womens_health_profile.user.get_full_name() or self.womens_health_profile.user.username
        return f"Daily Health Log - {self.date} - {user_name}"
    
    def save(self, *args, **kwargs):
        # Calculate data completeness
        self.calculate_data_completeness()
        super().save(*args, **kwargs)
    
    def calculate_data_completeness(self):
        """Calculate what percentage of daily health tracking was completed"""
        total_fields = 0
        completed_fields = 0
        
        # Core health fields
        core_fields = [
            'weight_kg', 'sleep_duration_hours', 'sleep_quality', 'water_intake_liters',
            'mood', 'stress_level', 'energy_level', 'exercise_performed'
        ]
        
        for field in core_fields:
            total_fields += 1
            field_value = getattr(self, field)
            if field_value is not None and field_value != False:
                completed_fields += 1
        
        # Women's health specific fields
        womens_health_fields = [
            'menstrual_flow', 'symptoms', 'medications_taken'
        ]
        
        for field in womens_health_fields:
            total_fields += 1
            field_value = getattr(self, field)
            if field_value is not None and field_value not in [False, [], '']:
                completed_fields += 1
        
        # Optional but valuable fields
        optional_fields = [
            'steps_count', 'emotional_wellbeing_score', 'self_care_activities'
        ]
        
        for field in optional_fields:
            total_fields += 1
            field_value = getattr(self, field)
            if field_value is not None and field_value not in [False, [], '']:
                completed_fields += 1
        
        self.data_completeness_score = int((float(completed_fields) / float(total_fields)) * 100) if total_fields > 0 else 0
    
    @property
    def health_score(self):
        """Calculate an overall health score for the day (0-10)"""
        score = 5  # Start with neutral score
        
        # Sleep quality impact
        if self.sleep_quality:
            sleep_scores = {
                'excellent': 2, 'good': 1, 'fair': 0, 'poor': -1, 'very_poor': -2
            }
            score += sleep_scores.get(self.sleep_quality, 0)
        
        # Exercise impact
        if self.exercise_performed:
            score += 1
        
        # Hydration impact
        if self.water_goal_met:
            score += 0.5
        
        # Mood impact
        if self.mood:
            mood_scores = {
                'excellent': 2, 'good': 1, 'neutral': 0, 'low': -1, 'poor': -2,
                'anxious': -1.5, 'stressed': -1.5, 'depressed': -2
            }
            score += mood_scores.get(self.mood, 0)
        
        # Stress impact
        if self.stress_level:
            stress_scores = {
                'very_low': 1, 'low': 0.5, 'moderate': 0, 'high': -1, 'very_high': -2
            }
            score += stress_scores.get(self.stress_level, 0)
        
        # Energy impact
        if self.energy_level:
            energy_scores = {
                'very_high': 1, 'high': 0.5, 'normal': 0, 'low': -0.5, 'very_low': -1
            }
            score += energy_scores.get(self.energy_level, 0)
        
        # Pain impact
        if self.pain_level:
            score -= min(self.pain_level * 0.2, 2)  # Max -2 for severe pain
        
        return max(0, min(10, score))  # Clamp between 0 and 10
    
    @property
    def bmi(self):
        """Calculate BMI if weight is available"""
        if not self.weight_kg:
            return None
        
        # Get height from user profile if available
        height_m = getattr(self.womens_health_profile.user, 'height_m', None)
        if not height_m:
            return None
        
        return round(self.weight_kg / (height_m ** 2), 1)
    
    @property
    def sleep_efficiency(self):
        """Calculate sleep efficiency if bedtime and wake time are available"""
        if not (self.sleep_bedtime and self.sleep_wake_time and self.sleep_duration_hours):
            return None
        
        # Calculate time in bed
        bedtime = timezone.datetime.combine(self.date, self.sleep_bedtime)
        wake_time = timezone.datetime.combine(self.date, self.sleep_wake_time)
        
        # Handle crossing midnight
        if wake_time < bedtime:
            wake_time += timezone.timedelta(days=1)
        
        time_in_bed_hours = (wake_time - bedtime).total_seconds() / 3600
        
        if time_in_bed_hours > 0:
            efficiency = (float(self.sleep_duration_hours) / time_in_bed_hours) * 100
            return round(efficiency, 1)
        
        return None
    
    def get_weekly_trends(self):
        """Get trends for the past week"""
        end_date = self.date
        start_date = end_date - timezone.timedelta(days=6)
        
        weekly_logs = DailyHealthLog.objects.filter(
            womens_health_profile=self.womens_health_profile,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        trends = {
            'weight_trend': [],
            'mood_trend': [],
            'energy_trend': [],
            'sleep_trend': [],
            'exercise_days': 0,
            'average_health_score': 0
        }
        
        total_health_score = 0
        score_count = 0
        
        for log in weekly_logs:
            if log.weight_kg:
                trends['weight_trend'].append({
                    'date': log.date.isoformat(),
                    'weight': float(log.weight_kg)
                })
            
            if log.mood:
                trends['mood_trend'].append({
                    'date': log.date.isoformat(),
                    'mood': log.mood
                })
            
            if log.energy_level:
                trends['energy_trend'].append({
                    'date': log.date.isoformat(),
                    'energy': log.energy_level
                })
            
            if log.sleep_duration_hours:
                trends['sleep_trend'].append({
                    'date': log.date.isoformat(),
                    'sleep_hours': float(log.sleep_duration_hours)
                })
            
            if log.exercise_performed:
                trends['exercise_days'] += 1
            
            health_score = log.health_score
            total_health_score += health_score
            score_count += 1
        
        if score_count > 0:
            trends['average_health_score'] = round(total_health_score / score_count, 1)
        
        return trends
    
    def get_summary(self):
        """Return daily health log summary for API responses"""
        return {
            'date': self.date.isoformat(),
            'health_score': self.health_score,
            'weight': float(self.weight_kg) if self.weight_kg else None,
            'bmi': self.bmi,
            'sleep': {
                'duration_hours': float(self.sleep_duration_hours) if self.sleep_duration_hours else None,
                'quality': self.sleep_quality,
                'efficiency': self.sleep_efficiency
            },
            'exercise': {
                'performed': self.exercise_performed,
                'duration_minutes': self.exercise_duration_minutes,
                'types': self.exercise_types
            },
            'mental_health': {
                'mood': self.mood,
                'stress_level': self.stress_level,
                'energy_level': self.energy_level,
                'emotional_wellbeing_score': self.emotional_wellbeing_score
            },
            'womens_health': {
                'menstrual_flow': self.menstrual_flow,
                'symptoms': self.symptoms,
                'pain_level': self.pain_level
            },
            'nutrition': {
                'water_intake_liters': float(self.water_intake_liters) if self.water_intake_liters else None,
                'water_goal_met': self.water_goal_met,
                'meals_count': self.meals_count,
                'vegetables_servings': self.vegetables_servings,
                'fruits_servings': self.fruits_servings
            },
            'data_completeness': f"{self.data_completeness_score}%",
            'goal_progress': self.goal_progress,
            'achievements': self.achievements
        }