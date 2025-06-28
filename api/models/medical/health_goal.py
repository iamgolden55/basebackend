# api/models/medical/health_goal.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from ..base import TimestampedModel
from .womens_health_profile import WomensHealthProfile


class HealthGoal(TimestampedModel):
    """
    Model for tracking health and wellness goals for women's health
    """
    # Relationship
    womens_health_profile = models.ForeignKey(
        WomensHealthProfile,
        on_delete=models.CASCADE,
        related_name='health_goals',
        help_text="Women's health profile this goal belongs to"
    )
    
    # Goal Basic Information
    title = models.CharField(
        max_length=200,
        help_text="Title/name of the health goal"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the goal"
    )
    
    # Goal Categories
    GOAL_CATEGORY_CHOICES = [
        ('fitness', 'Fitness & Exercise'),
        ('nutrition', 'Nutrition & Diet'),
        ('reproductive', 'Reproductive Health'),
        ('mental_health', 'Mental Health & Wellness'),
        ('preventive_care', 'Preventive Care'),
        ('weight_management', 'Weight Management'),
        ('sleep', 'Sleep & Rest'),
        ('stress_management', 'Stress Management'),
        ('hydration', 'Hydration'),
        ('medication_adherence', 'Medication Adherence'),
        ('lifestyle', 'Lifestyle Changes'),
        ('symptom_management', 'Symptom Management'),
        ('fertility', 'Fertility & Conception'),
        ('pregnancy', 'Pregnancy Health'),
        ('postpartum', 'Postpartum Recovery'),
        ('custom', 'Custom Goal')
    ]
    
    category = models.CharField(
        max_length=20,
        choices=GOAL_CATEGORY_CHOICES,
        help_text="Category of the health goal"
    )
    
    # Goal Type and Measurement
    GOAL_TYPE_CHOICES = [
        ('numeric', 'Numeric Target'),
        ('boolean', 'Yes/No Completion'),
        ('frequency', 'Frequency-based'),
        ('habit', 'Habit Formation'),
        ('milestone', 'Milestone Achievement')
    ]
    
    goal_type = models.CharField(
        max_length=15,
        choices=GOAL_TYPE_CHOICES,
        help_text="Type of goal measurement"
    )
    
    # Numeric Goals (e.g., lose 10 kg, drink 8 glasses of water)
    target_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Target numeric value for numeric goals"
    )
    
    current_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Current progress value"
    )
    
    unit_of_measurement = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Unit for measurement (kg, glasses, minutes, etc.)"
    )
    
    # Frequency Goals (e.g., exercise 3 times per week)
    target_frequency = models.IntegerField(
        null=True,
        blank=True,
        help_text="Target frequency for frequency-based goals"
    )
    
    FREQUENCY_PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ]
    
    frequency_period = models.CharField(
        max_length=15,
        choices=FREQUENCY_PERIOD_CHOICES,
        null=True,
        blank=True,
        help_text="Time period for frequency measurement"
    )
    
    current_frequency = models.IntegerField(
        default=0,
        help_text="Current frequency achieved in current period"
    )
    
    # Goal Timeline
    start_date = models.DateField(
        default=timezone.now,
        help_text="Date when goal was started"
    )
    
    target_date = models.DateField(
        null=True,
        blank=True,
        help_text="Target completion date"
    )
    
    completed_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when goal was completed"
    )
    
    # Goal Status
    GOAL_STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('overdue', 'Overdue')
    ]
    
    status = models.CharField(
        max_length=15,
        choices=GOAL_STATUS_CHOICES,
        default='active',
        help_text="Current status of the goal"
    )
    
    # Priority and Importance
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ]
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Priority level of the goal"
    )
    
    # Progress Tracking
    progress_percentage = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
        help_text="Progress percentage (0-100)"
    )
    
    # Streak Tracking
    current_streak = models.IntegerField(
        default=0,
        help_text="Current consecutive days/periods of goal achievement"
    )
    
    longest_streak = models.IntegerField(
        default=0,
        help_text="Longest streak achieved for this goal"
    )
    
    last_activity_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last progress update"
    )
    
    # Reminders and Notifications
    reminder_enabled = models.BooleanField(
        default=False,
        help_text="Whether reminders are enabled for this goal"
    )
    
    reminder_frequency = models.CharField(
        max_length=15,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('custom', 'Custom')
        ],
        null=True,
        blank=True,
        help_text="Frequency of reminders"
    )
    
    reminder_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Preferred time for reminders"
    )
    
    # Motivation and Support
    motivation_note = models.TextField(
        blank=True,
        null=True,
        help_text="Personal motivation or reason for this goal"
    )
    
    reward_for_completion = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Planned reward upon goal completion"
    )
    
    # Social and Support Features
    share_with_support_network = models.BooleanField(
        default=False,
        help_text="Whether to share progress with support network"
    )
    
    accountability_partner = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of accountability partner"
    )
    
    # Obstacles and Challenges
    potential_obstacles = models.JSONField(
        default=list,
        blank=True,
        help_text="List of potential obstacles or challenges"
    )
    
    strategies_to_overcome = models.JSONField(
        default=list,
        blank=True,
        help_text="Strategies to overcome obstacles"
    )
    
    # Goal Templates and Customization
    is_template_based = models.BooleanField(
        default=False,
        help_text="Whether this goal was created from a template"
    )
    
    template_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Name of template used if applicable"
    )
    
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom fields for specialized goal tracking"
    )
    
    # Health Professional Integration
    recommended_by_professional = models.BooleanField(
        default=False,
        help_text="Whether this goal was recommended by a healthcare professional"
    )
    
    professional_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of recommending healthcare professional"
    )
    
    professional_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes from healthcare professional about this goal"
    )
    
    # Analytics and Insights
    total_updates = models.IntegerField(
        default=0,
        help_text="Total number of progress updates"
    )
    
    average_daily_progress = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Average daily progress rate"
    )
    
    estimated_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="AI-estimated completion date based on current progress"
    )
    
    # Notes and Reflections
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="General notes about the goal"
    )
    
    success_factors = models.TextField(
        blank=True,
        null=True,
        help_text="Factors that contribute to success (filled upon completion)"
    )
    
    lessons_learned = models.TextField(
        blank=True,
        null=True,
        help_text="Lessons learned during goal pursuit"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_health_goals',
        help_text="User who created this goal"
    )
    
    last_updated_by = models.ForeignKey(
        'api.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_health_goals',
        help_text="User who last updated this goal"
    )
    
    class Meta:
        verbose_name = "Health Goal"
        verbose_name_plural = "Health Goals"
        indexes = [
            models.Index(fields=['womens_health_profile', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['target_date']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['start_date']),
        ]
        ordering = ['-created_at', 'priority', 'target_date']
    
    def __str__(self):
        return f"{self.title} - {self.womens_health_profile.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # Update progress percentage
        self.calculate_progress()
        
        # Update status based on dates and progress
        self.update_status()
        
        # Calculate average daily progress
        self.calculate_average_progress()
        
        # Estimate completion date
        self.estimate_completion_date()
        
        super().save(*args, **kwargs)
    
    def calculate_progress(self):
        """Calculate progress percentage based on goal type"""
        if self.goal_type == 'numeric' and self.target_value:
            if self.target_value > 0:
                self.progress_percentage = min(
                    int((self.current_value / self.target_value) * 100), 100
                )
            else:
                self.progress_percentage = 100 if self.current_value >= self.target_value else 0
        
        elif self.goal_type == 'frequency' and self.target_frequency:
            period_progress = min(self.current_frequency / self.target_frequency, 1.0)
            self.progress_percentage = int(period_progress * 100)
        
        elif self.goal_type == 'boolean':
            # For boolean goals, either 0% or 100%
            self.progress_percentage = 100 if self.status == 'completed' else 0
        
        elif self.goal_type == 'habit':
            # For habits, progress based on streak consistency
            days_since_start = (timezone.now().date() - self.start_date).days + 1
            if days_since_start > 0:
                consistency_rate = self.current_streak / days_since_start
                self.progress_percentage = min(int(consistency_rate * 100), 100)
    
    def update_status(self):
        """Update goal status based on current state"""
        if self.status in ['cancelled', 'completed']:
            return  # Don't change these statuses automatically
        
        if self.progress_percentage >= 100:
            self.status = 'completed'
            if not self.completed_date:
                self.completed_date = timezone.now().date()
        elif self.target_date and timezone.now().date() > self.target_date:
            self.status = 'overdue'
        else:
            self.status = 'active'
    
    def calculate_average_progress(self):
        """Calculate average daily progress rate"""
        if self.start_date:
            days_active = (timezone.now().date() - self.start_date).days + 1
            if days_active > 0 and self.total_updates > 0:
                self.average_daily_progress = self.current_value / days_active
    
    def estimate_completion_date(self):
        """Estimate completion date based on current progress rate"""
        if (self.goal_type == 'numeric' and self.target_value and 
            self.average_daily_progress and self.average_daily_progress > 0):
            
            remaining_value = self.target_value - self.current_value
            if remaining_value > 0:
                days_to_completion = remaining_value / self.average_daily_progress
                self.estimated_completion_date = timezone.now().date() + timezone.timedelta(
                    days=int(days_to_completion)
                )
    
    def update_progress(self, value, notes=None):
        """Update progress for this goal"""
        from .daily_health_log import DailyHealthLog  # Import here to avoid circular imports
        
        if self.goal_type == 'numeric':
            self.current_value = value
        elif self.goal_type == 'frequency':
            self.current_frequency += 1
        elif self.goal_type == 'boolean' and value:
            self.status = 'completed'
        
        # Update streak
        today = timezone.now().date()
        if self.last_activity_date == today - timezone.timedelta(days=1):
            self.current_streak += 1
        elif self.last_activity_date != today:
            self.current_streak = 1
        
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.last_activity_date = today
        self.total_updates += 1
        
        # Log the progress update
        try:
            daily_log, created = DailyHealthLog.objects.get_or_create(
                womens_health_profile=self.womens_health_profile,
                date=today,
                defaults={}
            )
            
            # Add goal progress to daily log
            goal_progress = daily_log.goal_progress or {}
            goal_progress[str(self.id)] = {
                'goal_title': self.title,
                'progress_value': float(value) if isinstance(value, (int, float)) else value,
                'notes': notes,
                'timestamp': timezone.now().isoformat()
            }
            daily_log.goal_progress = goal_progress
            daily_log.save()
        except Exception:
            pass  # Continue if daily log creation fails
        
        self.save()
    
    def reset_goal(self):
        """Reset goal progress"""
        self.current_value = 0
        self.current_frequency = 0
        self.progress_percentage = 0
        self.current_streak = 0
        self.status = 'active'
        self.completed_date = None
        self.last_activity_date = None
        self.total_updates = 0
        self.save()
    
    def pause_goal(self):
        """Pause the goal"""
        self.status = 'paused'
        self.save()
    
    def resume_goal(self):
        """Resume a paused goal"""
        if self.status == 'paused':
            self.status = 'active'
            self.save()
    
    def cancel_goal(self, reason=None):
        """Cancel the goal"""
        self.status = 'cancelled'
        if reason:
            self.notes = f"{self.notes}\n\nCancellation reason: {reason}" if self.notes else f"Cancellation reason: {reason}"
        self.save()
    
    @property
    def days_since_start(self):
        """Number of days since goal was started"""
        return (timezone.now().date() - self.start_date).days
    
    @property
    def days_until_target(self):
        """Number of days until target date"""
        if not self.target_date:
            return None
        
        today = timezone.now().date()
        if today > self.target_date:
            return 0  # Past target date
        
        return (self.target_date - today).days
    
    @property
    def is_overdue(self):
        """Check if goal is overdue"""
        return self.target_date and timezone.now().date() > self.target_date and self.status != 'completed'
    
    @property
    def completion_rate(self):
        """Calculate completion rate as decimal (0.0 to 1.0)"""
        return self.progress_percentage / 100.0
    
    def get_recent_progress(self, days=7):
        """Get recent progress updates for this goal"""
        from .daily_health_log import DailyHealthLog
        
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=days-1)
        
        daily_logs = DailyHealthLog.objects.filter(
            womens_health_profile=self.womens_health_profile,
            date__range=[start_date, end_date],
            goal_progress__has_key=str(self.id)
        ).order_by('date')
        
        progress_data = []
        for log in daily_logs:
            goal_data = log.goal_progress.get(str(self.id), {})
            progress_data.append({
                'date': log.date.isoformat(),
                'value': goal_data.get('progress_value'),
                'notes': goal_data.get('notes'),
                'timestamp': goal_data.get('timestamp')
            })
        
        return progress_data
    
    def get_goal_summary(self):
        """Return goal summary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'category': self.get_category_display(),
            'goal_type': self.get_goal_type_display(),
            'status': self.get_status_display(),
            'priority': self.get_priority_display(),
            'progress_percentage': self.progress_percentage,
            'current_value': float(self.current_value) if self.current_value else None,
            'target_value': float(self.target_value) if self.target_value else None,
            'unit': self.unit_of_measurement,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'start_date': self.start_date.isoformat(),
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'days_since_start': self.days_since_start,
            'days_until_target': self.days_until_target,
            'is_overdue': self.is_overdue,
            'last_activity': self.last_activity_date.isoformat() if self.last_activity_date else None,
            'estimated_completion': self.estimated_completion_date.isoformat() if self.estimated_completion_date else None
        }