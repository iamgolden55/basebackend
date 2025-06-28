# api/agent_modules/analytics/services.py

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Q
from api.models import MenstrualCycle, DailyHealthLog, FertilityTracking, WomensHealthProfile
import logging

logger = logging.getLogger(__name__)


class CycleAnalyticsService:
    """Service for analyzing menstrual cycle data and detecting irregularities."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CycleAnalyticsService")
    
    def initialize(self):
        """Initialize the cycle analytics service."""
        self.logger.info("Cycle Analytics Service initialized")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'service': 'CycleAnalyticsService',
            'status': 'active',
            'last_check': timezone.now().isoformat()
        }
    
    def detect_irregularities(self, user_id: int, months_back: int = 6) -> Dict[str, Any]:
        """
        Detect cycle irregularities for a user.
        
        Args:
            user_id: User ID to analyze
            months_back: Number of months to look back
            
        Returns:
            Dictionary with irregularity analysis
        """
        try:
            profile = WomensHealthProfile.objects.get(user_id=user_id)
            
            # Get recent cycles
            cutoff_date = timezone.now().date() - timedelta(days=months_back * 30)
            cycles = MenstrualCycle.objects.filter(
                womens_health_profile=profile,
                cycle_start_date__gte=cutoff_date
            ).order_by('cycle_start_date')
            
            if cycles.count() < 3:
                return {
                    'sufficient_data': False,
                    'message': 'Need at least 3 cycles for analysis',
                    'cycles_count': cycles.count()
                }
            
            # Analyze cycle lengths
            cycle_lengths = [c.cycle_length for c in cycles if c.cycle_length]
            avg_length = sum(cycle_lengths) / len(cycle_lengths) if cycle_lengths else 0
            
            # Detect irregularities
            irregularities = []
            
            # Long cycles (>35 days)
            long_cycles = [l for l in cycle_lengths if l > 35]
            if long_cycles:
                irregularities.append({
                    'type': 'long_cycles',
                    'severity': 'moderate' if len(long_cycles) < len(cycle_lengths) / 2 else 'high',
                    'description': f'{len(long_cycles)} cycles longer than 35 days',
                    'recommendation': 'Consider consulting healthcare provider'
                })
            
            # Short cycles (<21 days)
            short_cycles = [l for l in cycle_lengths if l < 21]
            if short_cycles:
                irregularities.append({
                    'type': 'short_cycles',
                    'severity': 'moderate' if len(short_cycles) < len(cycle_lengths) / 2 else 'high',
                    'description': f'{len(short_cycles)} cycles shorter than 21 days',
                    'recommendation': 'Consider consulting healthcare provider'
                })
            
            # High variability (standard deviation > 7 days)
            if len(cycle_lengths) > 2:
                variance = sum((x - avg_length) ** 2 for x in cycle_lengths) / len(cycle_lengths)
                std_dev = variance ** 0.5
                
                if std_dev > 7:
                    irregularities.append({
                        'type': 'high_variability',
                        'severity': 'moderate',
                        'description': f'High cycle length variation (±{std_dev:.1f} days)',
                        'recommendation': 'Track consistently to identify patterns'
                    })
            
            # Missed periods (gaps > 50 days)
            missed_periods = self._detect_missed_periods(cycles)
            if missed_periods:
                irregularities.append({
                    'type': 'missed_periods',
                    'severity': 'high',
                    'description': f'{len(missed_periods)} potential missed periods',
                    'recommendation': 'Consult healthcare provider immediately'
                })
            
            return {
                'sufficient_data': True,
                'analysis_period': f'{months_back} months',
                'cycles_analyzed': len(cycles),
                'average_cycle_length': round(avg_length, 1),
                'irregularities_detected': len(irregularities),
                'irregularities': irregularities,
                'overall_assessment': self._get_overall_assessment(irregularities),
                'next_expected_period': self._predict_next_period_simple(cycles)
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting irregularities for user {user_id}: {e}")
            raise
    
    def analyze_patterns(self, user_id: int, data_type: str, days_back: int = 90) -> Dict[str, Any]:
        """
        Analyze patterns in user's health data.
        
        Args:
            user_id: User ID to analyze
            data_type: Type of data to analyze
            days_back: Number of days to look back
            
        Returns:
            Dictionary with pattern analysis
        """
        try:
            profile = WomensHealthProfile.objects.get(user_id=user_id)
            cutoff_date = timezone.now().date() - timedelta(days=days_back)
            
            if data_type == 'mood':
                return self._analyze_mood_patterns(profile, cutoff_date)
            elif data_type == 'energy':
                return self._analyze_energy_patterns(profile, cutoff_date)
            elif data_type == 'symptoms':
                return self._analyze_symptom_patterns(profile, cutoff_date)
            elif data_type == 'sleep':
                return self._analyze_sleep_patterns(profile, cutoff_date)
            else:
                return {'error': f'Unsupported data type: {data_type}'}
                
        except Exception as e:
            self.logger.error(f"Error analyzing patterns for user {user_id}: {e}")
            raise
    
    def _detect_missed_periods(self, cycles) -> List[Dict[str, Any]]:
        """Detect potential missed periods based on gaps in cycle data."""
        missed = []
        cycles_list = list(cycles)
        
        for i in range(len(cycles_list) - 1):
            current = cycles_list[i]
            next_cycle = cycles_list[i + 1]
            
            gap_days = (next_cycle.cycle_start_date - current.cycle_start_date).days
            
            if gap_days > 50:  # Potential missed period
                missed.append({
                    'gap_start': current.cycle_start_date.isoformat(),
                    'gap_end': next_cycle.cycle_start_date.isoformat(),
                    'gap_days': gap_days
                })
        
        return missed
    
    def _get_overall_assessment(self, irregularities: List[Dict]) -> str:
        """Get overall assessment based on detected irregularities."""
        if not irregularities:
            return 'Regular cycles detected'
        
        high_severity = any(irr['severity'] == 'high' for irr in irregularities)
        if high_severity:
            return 'Significant irregularities detected - consult healthcare provider'
        
        return 'Some irregularities detected - monitor and track consistently'
    
    def _predict_next_period_simple(self, cycles) -> Optional[str]:
        """Simple prediction of next period based on average cycle length."""
        if not cycles:
            return None
        
        last_cycle = cycles.last()
        cycle_lengths = [c.cycle_length for c in cycles if c.cycle_length]
        
        if not cycle_lengths:
            return None
        
        avg_length = sum(cycle_lengths) / len(cycle_lengths)
        next_period = last_cycle.cycle_start_date + timedelta(days=int(avg_length))
        
        return next_period.isoformat()
    
    def _analyze_mood_patterns(self, profile, cutoff_date) -> Dict[str, Any]:
        """Analyze mood patterns from daily health logs."""
        logs = DailyHealthLog.objects.filter(
            womens_health_profile=profile,
            date__gte=cutoff_date,
            mood__isnull=False
        ).order_by('date')
        
        if not logs:
            return {'error': 'No mood data available'}
        
        # Analyze mood distribution
        mood_counts = {}
        for log in logs:
            mood_counts[log.mood] = mood_counts.get(log.mood, 0) + 1
        
        # Find most common mood
        most_common_mood = max(mood_counts, key=mood_counts.get)
        
        # Analyze cycle-related patterns
        cycle_patterns = self._analyze_mood_by_cycle_phase(profile, logs)
        
        return {
            'data_type': 'mood',
            'analysis_period_days': (timezone.now().date() - cutoff_date).days,
            'total_entries': logs.count(),
            'mood_distribution': mood_counts,
            'most_common_mood': most_common_mood,
            'cycle_patterns': cycle_patterns,
            'trends': self._calculate_mood_trends(logs)
        }
    
    def _analyze_energy_patterns(self, profile, cutoff_date) -> Dict[str, Any]:
        """Analyze energy level patterns."""
        logs = DailyHealthLog.objects.filter(
            womens_health_profile=profile,
            date__gte=cutoff_date,
            energy_level__isnull=False
        ).order_by('date')
        
        if not logs:
            return {'error': 'No energy data available'}
        
        # Analyze energy distribution
        energy_counts = {}
        for log in logs:
            energy_counts[log.energy_level] = energy_counts.get(log.energy_level, 0) + 1
        
        return {
            'data_type': 'energy',
            'analysis_period_days': (timezone.now().date() - cutoff_date).days,
            'total_entries': logs.count(),
            'energy_distribution': energy_counts,
            'patterns': self._find_energy_patterns(logs)
        }
    
    def _analyze_symptom_patterns(self, profile, cutoff_date) -> Dict[str, Any]:
        """Analyze symptom patterns."""
        logs = DailyHealthLog.objects.filter(
            womens_health_profile=profile,
            date__gte=cutoff_date
        ).exclude(symptoms=[]).order_by('date')
        
        if not logs:
            return {'error': 'No symptom data available'}
        
        # Collect all symptoms
        all_symptoms = []
        for log in logs:
            all_symptoms.extend(log.symptoms)
        
        # Count symptom frequency
        symptom_counts = {}
        for symptom in all_symptoms:
            symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1
        
        return {
            'data_type': 'symptoms',
            'analysis_period_days': (timezone.now().date() - cutoff_date).days,
            'total_entries': logs.count(),
            'symptom_frequency': symptom_counts,
            'most_common_symptoms': sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def _analyze_sleep_patterns(self, profile, cutoff_date) -> Dict[str, Any]:
        """Analyze sleep patterns."""
        logs = DailyHealthLog.objects.filter(
            womens_health_profile=profile,
            date__gte=cutoff_date,
            sleep_duration_hours__isnull=False
        ).order_by('date')
        
        if not logs:
            return {'error': 'No sleep data available'}
        
        # Calculate sleep statistics
        sleep_durations = [float(log.sleep_duration_hours) for log in logs]
        avg_sleep = sum(sleep_durations) / len(sleep_durations)
        
        return {
            'data_type': 'sleep',
            'analysis_period_days': (timezone.now().date() - cutoff_date).days,
            'total_entries': logs.count(),
            'average_sleep_hours': round(avg_sleep, 1),
            'sleep_quality_distribution': self._get_sleep_quality_distribution(logs),
            'sleep_trends': self._calculate_sleep_trends(logs)
        }
    
    def _analyze_mood_by_cycle_phase(self, profile, logs) -> Dict[str, Any]:
        """Analyze mood patterns by menstrual cycle phase."""
        # This would require more complex logic to map dates to cycle phases
        # For now, return placeholder structure
        return {
            'menstrual_phase': 'Analysis pending',
            'follicular_phase': 'Analysis pending',
            'ovulation_phase': 'Analysis pending',
            'luteal_phase': 'Analysis pending'
        }
    
    def _calculate_mood_trends(self, logs) -> Dict[str, Any]:
        """Calculate mood trends over time."""
        # Simplified trend analysis
        recent_logs = list(logs.order_by('-date')[:7])  # Last 7 days
        older_logs = list(logs.order_by('-date')[7:14])  # Previous 7 days
        
        if len(recent_logs) < 3 or len(older_logs) < 3:
            return {'trend': 'insufficient_data'}
        
        # Simple trend analysis based on mood scores
        mood_scores = {
            'excellent': 5, 'good': 4, 'neutral': 3, 'low': 2, 'poor': 1,
            'anxious': 2, 'stressed': 2, 'depressed': 1
        }
        
        recent_avg = sum(mood_scores.get(log.mood, 3) for log in recent_logs) / len(recent_logs)
        older_avg = sum(mood_scores.get(log.mood, 3) for log in older_logs) / len(older_logs)
        
        if recent_avg > older_avg + 0.5:
            return {'trend': 'improving', 'direction': 'up'}
        elif recent_avg < older_avg - 0.5:
            return {'trend': 'declining', 'direction': 'down'}
        else:
            return {'trend': 'stable', 'direction': 'neutral'}
    
    def _find_energy_patterns(self, logs) -> Dict[str, Any]:
        """Find patterns in energy levels."""
        # Analyze by day of week
        day_patterns = {}
        for log in logs:
            day_name = log.date.strftime('%A')
            if day_name not in day_patterns:
                day_patterns[day_name] = []
            day_patterns[day_name].append(log.energy_level)
        
        return {
            'day_of_week_patterns': day_patterns,
            'weekly_insights': self._get_weekly_energy_insights(day_patterns)
        }
    
    def _get_sleep_quality_distribution(self, logs) -> Dict[str, int]:
        """Get distribution of sleep quality ratings."""
        quality_counts = {}
        for log in logs:
            if log.sleep_quality:
                quality_counts[log.sleep_quality] = quality_counts.get(log.sleep_quality, 0) + 1
        return quality_counts
    
    def _calculate_sleep_trends(self, logs) -> Dict[str, Any]:
        """Calculate sleep trends over time."""
        # Simplified trend calculation
        recent_logs = list(logs.order_by('-date')[:7])
        if len(recent_logs) < 5:
            return {'trend': 'insufficient_data'}
        
        recent_avg = sum(float(log.sleep_duration_hours) for log in recent_logs) / len(recent_logs)
        
        return {
            'recent_average_hours': round(recent_avg, 1),
            'trend': 'stable'  # Simplified for now
        }
    
    def _get_weekly_energy_insights(self, day_patterns) -> List[str]:
        """Generate insights about weekly energy patterns."""
        insights = []
        
        # Find highest and lowest energy days
        if day_patterns:
            energy_scores = {
                'very_high': 5, 'high': 4, 'normal': 3, 'low': 2, 'very_low': 1
            }
            
            day_averages = {}
            for day, energy_levels in day_patterns.items():
                if energy_levels:
                    avg_score = sum(energy_scores.get(level, 3) for level in energy_levels) / len(energy_levels)
                    day_averages[day] = avg_score
            
            if day_averages:
                highest_day = max(day_averages, key=day_averages.get)
                lowest_day = min(day_averages, key=day_averages.get)
                
                insights.append(f"Highest energy typically on {highest_day}")
                insights.append(f"Lowest energy typically on {lowest_day}")
        
        return insights


class HealthPredictionService:
    """Service for generating health predictions and insights."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.HealthPredictionService")
    
    def initialize(self):
        """Initialize the health prediction service."""
        self.logger.info("Health Prediction Service initialized")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'service': 'HealthPredictionService',
            'status': 'active',
            'last_check': timezone.now().isoformat()
        }
    
    def predict_next_period(self, user_id: int) -> Dict[str, Any]:
        """Predict user's next menstrual period."""
        try:
            profile = WomensHealthProfile.objects.get(user_id=user_id)
            
            # Get recent cycles for prediction
            recent_cycles = MenstrualCycle.objects.filter(
                womens_health_profile=profile
            ).order_by('-cycle_start_date')[:6]
            
            if not recent_cycles:
                return {
                    'prediction_available': False,
                    'reason': 'No cycle data available'
                }
            
            # Calculate prediction based on average cycle length
            cycle_lengths = [c.cycle_length for c in recent_cycles if c.cycle_length]
            
            if not cycle_lengths:
                # Use profile average if no recent cycle lengths
                avg_length = profile.average_cycle_length
            else:
                avg_length = sum(cycle_lengths) / len(cycle_lengths)
            
            last_cycle = recent_cycles.first()
            predicted_date = last_cycle.cycle_start_date + timedelta(days=int(avg_length))
            
            # Calculate confidence based on cycle regularity
            confidence = self._calculate_prediction_confidence(cycle_lengths, avg_length)
            
            return {
                'prediction_available': True,
                'predicted_date': predicted_date.isoformat(),
                'confidence_level': confidence,
                'average_cycle_length': round(avg_length, 1),
                'last_period_date': last_cycle.cycle_start_date.isoformat(),
                'cycles_used_for_prediction': len(cycle_lengths) or 1
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting next period for user {user_id}: {e}")
            raise
    
    def predict_fertility_window(self, user_id: int) -> Dict[str, Any]:
        """Predict user's fertility window."""
        try:
            profile = WomensHealthProfile.objects.get(user_id=user_id)
            
            # Get next period prediction first
            period_prediction = self.predict_next_period(user_id)
            
            if not period_prediction['prediction_available']:
                return {
                    'prediction_available': False,
                    'reason': 'Cannot predict fertility without cycle data'
                }
            
            predicted_period = datetime.fromisoformat(period_prediction['predicted_date']).date()
            avg_length = period_prediction['average_cycle_length']
            
            # Calculate ovulation (typically 14 days before next period)
            ovulation_day = max(1, int(avg_length - 14))
            
            # Get recent fertility tracking data for better prediction
            recent_tracking = FertilityTracking.objects.filter(
                womens_health_profile=profile
            ).order_by('-date')[:30]
            
            # Adjust prediction based on fertility tracking patterns
            if recent_tracking:
                ovulation_adjustment = self._analyze_ovulation_patterns(recent_tracking)
                ovulation_day += ovulation_adjustment
            
            last_cycle_start = datetime.fromisoformat(period_prediction['last_period_date']).date()
            predicted_ovulation = last_cycle_start + timedelta(days=ovulation_day)
            
            # Fertility window: 5 days before ovulation + ovulation day
            fertile_start = predicted_ovulation - timedelta(days=5)
            fertile_end = predicted_ovulation
            
            return {
                'prediction_available': True,
                'fertile_window': {
                    'start_date': fertile_start.isoformat(),
                    'end_date': fertile_end.isoformat(),
                    'ovulation_date': predicted_ovulation.isoformat()
                },
                'confidence_level': period_prediction['confidence_level'],
                'days_until_ovulation': (predicted_ovulation - timezone.now().date()).days,
                'fertility_tracking_data_available': recent_tracking.exists()
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting fertility window for user {user_id}: {e}")
            raise
    
    def generate_health_insights(self, user_id: int) -> Dict[str, Any]:
        """Generate comprehensive health insights for a user."""
        try:
            profile = WomensHealthProfile.objects.get(user_id=user_id)
            
            insights = {
                'user_id': user_id,
                'generated_at': timezone.now().isoformat(),
                'insights': []
            }
            
            # Cycle-related insights
            cycle_insights = self._generate_cycle_insights(profile)
            insights['insights'].extend(cycle_insights)
            
            # Health pattern insights
            pattern_insights = self._generate_pattern_insights(profile)
            insights['insights'].extend(pattern_insights)
            
            # Goal progress insights
            goal_insights = self._generate_goal_insights(profile)
            insights['insights'].extend(goal_insights)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating health insights for user {user_id}: {e}")
            raise
    
    def assess_health_risks(self, user_id: int) -> Dict[str, Any]:
        """Assess health risks for a user based on their data."""
        try:
            profile = WomensHealthProfile.objects.get(user_id=user_id)
            
            risks = {
                'user_id': user_id,
                'assessment_date': timezone.now().isoformat(),
                'risk_factors': [],
                'recommendations': []
            }
            
            # Age-related risks
            user_age = self._calculate_user_age(profile.user)
            if user_age:
                age_risks = self._assess_age_related_risks(user_age, profile)
                risks['risk_factors'].extend(age_risks)
            
            # Family history risks
            family_risks = self._assess_family_history_risks(profile)
            risks['risk_factors'].extend(family_risks)
            
            # Lifestyle risks
            lifestyle_risks = self._assess_lifestyle_risks(profile)
            risks['risk_factors'].extend(lifestyle_risks)
            
            # Medical condition risks
            condition_risks = self._assess_medical_condition_risks(profile)
            risks['risk_factors'].extend(condition_risks)
            
            # Generate recommendations based on identified risks
            risks['recommendations'] = self._generate_risk_based_recommendations(risks['risk_factors'])
            
            return risks
            
        except Exception as e:
            self.logger.error(f"Error assessing health risks for user {user_id}: {e}")
            raise
    
    def _calculate_prediction_confidence(self, cycle_lengths: List[int], avg_length: float) -> str:
        """Calculate confidence level for predictions based on cycle regularity."""
        if not cycle_lengths or len(cycle_lengths) < 3:
            return 'low'
        
        # Calculate variability
        variance = sum((x - avg_length) ** 2 for x in cycle_lengths) / len(cycle_lengths)
        std_dev = variance ** 0.5
        
        if std_dev <= 3:
            return 'high'
        elif std_dev <= 7:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_ovulation_patterns(self, tracking_data) -> int:
        """Analyze fertility tracking data to adjust ovulation prediction."""
        # Simplified analysis - look for positive ovulation tests
        positive_tests = [t for t in tracking_data if t.ovulation_test_result == 'positive']
        
        if positive_tests:
            # Calculate average cycle day for positive tests
            cycle_days = [t.cycle_day for t in positive_tests if t.cycle_day]
            if cycle_days:
                avg_ovulation_day = sum(cycle_days) / len(cycle_days)
                # Adjust from standard day 14 assumption
                return int(avg_ovulation_day - 14)
        
        return 0  # No adjustment
    
    def _generate_cycle_insights(self, profile) -> List[Dict[str, Any]]:
        """Generate insights related to menstrual cycles."""
        insights = []
        
        # Recent cycle analysis
        recent_cycles = MenstrualCycle.objects.filter(
            womens_health_profile=profile
        ).order_by('-cycle_start_date')[:3]
        
        if recent_cycles.count() >= 2:
            last_cycle = recent_cycles.first()
            prev_cycle = list(recent_cycles)[1]
            
            if last_cycle.cycle_length and prev_cycle.cycle_length:
                length_diff = last_cycle.cycle_length - prev_cycle.cycle_length
                
                if abs(length_diff) > 7:
                    insights.append({
                        'type': 'cycle_variability',
                        'severity': 'medium',
                        'title': 'Cycle Length Variation Detected',
                        'description': f'Your last cycle was {abs(length_diff)} days {"longer" if length_diff > 0 else "shorter"} than usual',
                        'recommendation': 'Continue tracking to identify patterns'
                    })
        
        return insights
    
    def _generate_pattern_insights(self, profile) -> List[Dict[str, Any]]:
        """Generate insights from health pattern analysis."""
        insights = []
        
        # Analyze recent health logs for patterns
        recent_logs = DailyHealthLog.objects.filter(
            womens_health_profile=profile,
            date__gte=timezone.now().date() - timedelta(days=30)
        )
        
        if recent_logs.exists():
            # Sleep pattern insight
            sleep_logs = recent_logs.filter(sleep_duration_hours__isnull=False)
            if sleep_logs.count() > 5:
                avg_sleep = sleep_logs.aggregate(avg=Avg('sleep_duration_hours'))['avg']
                if avg_sleep < 7:
                    insights.append({
                        'type': 'sleep_pattern',
                        'severity': 'medium',
                        'title': 'Low Sleep Duration Detected',
                        'description': f'Your average sleep is {avg_sleep:.1f} hours - consider aiming for 7-9 hours',
                        'recommendation': 'Establish a consistent bedtime routine'
                    })
        
        return insights
    
    def _generate_goal_insights(self, profile) -> List[Dict[str, Any]]:
        """Generate insights related to health goals."""
        insights = []
        
        # Analyze active goals
        from api.models.medical.health_goal import HealthGoal
        
        active_goals = HealthGoal.objects.filter(
            womens_health_profile=profile,
            status='active'
        )
        
        for goal in active_goals:
            if goal.progress_percentage > 75:
                insights.append({
                    'type': 'goal_progress',
                    'severity': 'low',
                    'title': f'Great Progress on {goal.title}',
                    'description': f'You\'re {goal.progress_percentage}% complete - keep it up!',
                    'recommendation': 'Stay consistent to reach your goal'
                })
            elif goal.is_overdue:
                insights.append({
                    'type': 'goal_overdue',
                    'severity': 'medium',
                    'title': f'Goal Behind Schedule: {goal.title}',
                    'description': 'Consider adjusting your target date or breaking the goal into smaller steps',
                    'recommendation': 'Review and adjust your goal strategy'
                })
        
        return insights
    
    def _calculate_user_age(self, user) -> Optional[int]:
        """Calculate user's age from date of birth."""
        if hasattr(user, 'date_of_birth') and user.date_of_birth:
            today = timezone.now().date()
            return today.year - user.date_of_birth.year - ((today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day))
        return None
    
    def _assess_age_related_risks(self, age: int, profile) -> List[Dict[str, Any]]:
        """Assess age-related health risks."""
        risks = []
        
        if age >= 40:
            risks.append({
                'type': 'age_related',
                'risk_level': 'medium',
                'factor': 'Increased breast cancer screening needs',
                'description': f'At age {age}, annual mammograms are recommended'
            })
        
        if age >= 50:
            risks.append({
                'type': 'age_related',
                'risk_level': 'medium',
                'factor': 'Menopause transition',
                'description': 'Monitor for menopause-related changes'
            })
        
        return risks
    
    def _assess_family_history_risks(self, profile) -> List[Dict[str, Any]]:
        """Assess risks based on family history."""
        risks = []
        
        if profile.family_history_breast_cancer:
            risks.append({
                'type': 'family_history',
                'risk_level': 'high',
                'factor': 'Family history of breast cancer',
                'description': 'Consider genetic counseling and enhanced screening'
            })
        
        if profile.family_history_ovarian_cancer:
            risks.append({
                'type': 'family_history',
                'risk_level': 'high',
                'factor': 'Family history of ovarian cancer',
                'description': 'Discuss BRCA testing with healthcare provider'
            })
        
        return risks
    
    def _assess_lifestyle_risks(self, profile) -> List[Dict[str, Any]]:
        """Assess lifestyle-related risks."""
        risks = []
        
        if profile.exercise_frequency in ['rarely', 'never']:
            risks.append({
                'type': 'lifestyle',
                'risk_level': 'medium',
                'factor': 'Low physical activity',
                'description': 'Regular exercise reduces risk of various health conditions'
            })
        
        if profile.stress_level in ['high', 'severe']:
            risks.append({
                'type': 'lifestyle',
                'risk_level': 'medium',
                'factor': 'High stress levels',
                'description': 'Chronic stress can impact hormonal balance and overall health'
            })
        
        return risks
    
    def _assess_medical_condition_risks(self, profile) -> List[Dict[str, Any]]:
        """Assess risks based on existing medical conditions."""
        risks = []
        
        if profile.diabetes:
            risks.append({
                'type': 'medical_condition',
                'risk_level': 'high',
                'factor': 'Diabetes',
                'description': 'Requires regular monitoring and may affect pregnancy planning'
            })
        
        if profile.hypertension:
            risks.append({
                'type': 'medical_condition',
                'risk_level': 'medium',
                'factor': 'Hypertension',
                'description': 'Monitor blood pressure regularly and during pregnancy'
            })
        
        if profile.pcos:
            risks.append({
                'type': 'medical_condition',
                'risk_level': 'medium',
                'factor': 'PCOS',
                'description': 'May affect fertility and increase diabetes risk'
            })
        
        return risks
    
    def _generate_risk_based_recommendations(self, risk_factors: List[Dict]) -> List[str]:
        """Generate recommendations based on identified risk factors."""
        recommendations = []
        
        risk_types = [r['type'] for r in risk_factors]
        
        if 'family_history' in risk_types:
            recommendations.append('Discuss family history with healthcare provider')
            recommendations.append('Consider genetic counseling if multiple family cancers')
        
        if 'lifestyle' in risk_types:
            recommendations.append('Implement stress reduction techniques')
            recommendations.append('Aim for 150 minutes of moderate exercise weekly')
        
        if 'medical_condition' in risk_types:
            recommendations.append('Maintain regular follow-ups with healthcare providers')
            recommendations.append('Keep medical conditions well-controlled')
        
        if 'age_related' in risk_types:
            recommendations.append('Stay up-to-date with age-appropriate screenings')
        
        return recommendations


class RecommendationService:
    """Service for generating personalized health recommendations."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.RecommendationService")
    
    def initialize(self):
        """Initialize the recommendation service."""
        self.logger.info("Recommendation Service initialized")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'service': 'RecommendationService',
            'status': 'active',
            'last_check': timezone.now().isoformat()
        }
    
    def generate_personalized_recommendations(self, user_id: int) -> Dict[str, Any]:
        """Generate personalized health recommendations for a user."""
        try:
            profile = WomensHealthProfile.objects.get(user_id=user_id)
            
            recommendations = {
                'user_id': user_id,
                'generated_at': timezone.now().isoformat(),
                'categories': {
                    'cycle_tracking': self._get_cycle_tracking_recommendations(profile),
                    'lifestyle': self._get_lifestyle_recommendations(profile),
                    'screenings': self._get_screening_recommendations(profile),
                    'goals': self._get_goal_recommendations(profile)
                }
            }
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations for user {user_id}: {e}")
            raise
    
    def _get_cycle_tracking_recommendations(self, profile) -> List[Dict[str, Any]]:
        """Get cycle tracking recommendations."""
        recommendations = []
        
        # Check recent cycle data completeness
        recent_cycles = MenstrualCycle.objects.filter(
            womens_health_profile=profile
        ).order_by('-cycle_start_date')[:3]
        
        if recent_cycles.count() < 3:
            recommendations.append({
                'title': 'Start Consistent Cycle Tracking',
                'description': 'Track at least 3 cycles to establish patterns and get predictions',
                'priority': 'high',
                'category': 'tracking'
            })
        
        # Check for fertility tracking if trying to conceive
        if profile.pregnancy_status == 'trying_to_conceive' and not profile.fertility_tracking_enabled:
            recommendations.append({
                'title': 'Enable Fertility Tracking',
                'description': 'Track ovulation signs to maximize conception chances',
                'priority': 'high',
                'category': 'fertility'
            })
        
        return recommendations
    
    def _get_lifestyle_recommendations(self, profile) -> List[Dict[str, Any]]:
        """Get lifestyle recommendations."""
        recommendations = []
        
        # Exercise recommendations
        if profile.exercise_frequency in ['rarely', 'never']:
            recommendations.append({
                'title': 'Increase Physical Activity',
                'description': 'Aim for 150 minutes of moderate exercise per week',
                'priority': 'medium',
                'category': 'exercise'
            })
        
        # Stress management
        if profile.stress_level in ['high', 'severe']:
            recommendations.append({
                'title': 'Implement Stress Management',
                'description': 'Try meditation, yoga, or other stress-reduction techniques',
                'priority': 'medium',
                'category': 'stress'
            })
        
        # Sleep recommendations based on recent logs
        recent_logs = DailyHealthLog.objects.filter(
            womens_health_profile=profile,
            date__gte=timezone.now().date() - timedelta(days=7),
            sleep_duration_hours__isnull=False
        )
        
        if recent_logs.exists():
            avg_sleep = recent_logs.aggregate(avg=Avg('sleep_duration_hours'))['avg']
            if avg_sleep and avg_sleep < 7:
                recommendations.append({
                    'title': 'Improve Sleep Duration',
                    'description': f'Your average sleep is {avg_sleep:.1f}h - aim for 7-9 hours',
                    'priority': 'medium',
                    'category': 'sleep'
                })
        
        return recommendations
    
    def _get_screening_recommendations(self, profile) -> List[Dict[str, Any]]:
        """Get health screening recommendations."""
        recommendations = []
        
        # Pap smear recommendations
        if profile.last_pap_smear:
            days_since_pap = (timezone.now().date() - profile.last_pap_smear).days
            if days_since_pap > 1095:  # 3 years
                recommendations.append({
                    'title': 'Schedule Pap Smear',
                    'description': 'It\'s been over 3 years since your last pap smear',
                    'priority': 'high',
                    'category': 'screening'
                })
        else:
            recommendations.append({
                'title': 'Schedule First Pap Smear',
                'description': 'Regular pap smears are important for cervical health',
                'priority': 'medium',
                'category': 'screening'
            })
        
        # Mammogram recommendations based on age and family history
        user_age = self._calculate_user_age(profile.user)
        if user_age and user_age >= 40:
            if profile.last_mammogram:
                days_since_mammo = (timezone.now().date() - profile.last_mammogram).days
                if days_since_mammo > 365:  # 1 year
                    recommendations.append({
                        'title': 'Schedule Annual Mammogram',
                        'description': 'Annual mammograms are recommended after age 40',
                        'priority': 'high',
                        'category': 'screening'
                    })
            else:
                recommendations.append({
                    'title': 'Schedule First Mammogram',
                    'description': 'Start annual mammograms at age 40 or earlier if family history',
                    'priority': 'high',
                    'category': 'screening'
                })
        
        return recommendations
    
    def _get_goal_recommendations(self, profile) -> List[Dict[str, Any]]:
        """Get health goal recommendations."""
        recommendations = []
        
        from api.models.medical.health_goal import HealthGoal
        
        # Check if user has any active goals
        active_goals = HealthGoal.objects.filter(
            womens_health_profile=profile,
            status='active'
        ).count()
        
        if active_goals == 0:
            recommendations.append({
                'title': 'Set Your First Health Goal',
                'description': 'Setting goals helps track progress and stay motivated',
                'priority': 'medium',
                'category': 'goals'
            })
        elif active_goals > 5:
            recommendations.append({
                'title': 'Focus on Fewer Goals',
                'description': 'Consider focusing on 3-5 goals for better success rates',
                'priority': 'low',
                'category': 'goals'
            })
        
        # Suggest specific goals based on profile data
        if profile.pregnancy_status == 'trying_to_conceive':
            recommendations.append({
                'title': 'Set Preconception Health Goals',
                'description': 'Consider goals for folic acid, healthy weight, and exercise',
                'priority': 'high',
                'category': 'goals'
            })
        
        return recommendations
    
    def _calculate_user_age(self, user) -> Optional[int]:
        """Calculate user's age from date of birth."""
        if hasattr(user, 'date_of_birth') and user.date_of_birth:
            today = timezone.now().date()
            return today.year - user.date_of_birth.year - ((today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day))
        return None