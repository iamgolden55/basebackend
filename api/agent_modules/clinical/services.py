# api/agent_modules/clinical/services.py

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg
from api.models import Appointment, HealthScreening, MedicalHistory, WomensHealthProfile
import logging

logger = logging.getLogger(__name__)


class HealthScreeningService:
    """Service for managing health screening recommendations and schedules."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.HealthScreeningService")
    
    def initialize(self):
        """Initialize the health screening service."""
        self.logger.info("Health Screening Service initialized")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'service': 'HealthScreeningService',
            'status': 'active',
            'last_check': timezone.now().isoformat()
        }
    
    def get_screening_recommendations(self, user_id: int) -> Dict[str, Any]:
        """
        Get personalized health screening recommendations.
        
        Args:
            user_id: User ID to get recommendations for
            
        Returns:
            Dictionary with screening recommendations
        """
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            user = User.objects.get(id=user_id)
            profile = WomensHealthProfile.objects.get(user=user)
            
            # Calculate user's age
            birth_date = getattr(user, 'birth_date', None)
            if birth_date:
                age = (timezone.now().date() - birth_date).days // 365
            else:
                age = profile.age if hasattr(profile, 'age') else 25  # Default age
            
            recommendations = {
                'user_id': user_id,
                'age': age,
                'screening_recommendations': [],
                'urgent_screenings': [],
                'routine_screenings': [],
                'lifestyle_recommendations': []
            }
            
            # Age-based screening recommendations
            screening_guidelines = self._get_age_based_guidelines(age)
            
            for guideline in screening_guidelines:
                # Check if screening is due
                last_screening = self._get_last_screening(user_id, guideline['type'])
                
                if self._is_screening_due(guideline, last_screening):
                    screening_rec = {
                        'screening_type': guideline['type'],
                        'recommended_frequency': guideline['frequency'],
                        'priority': guideline['priority'],
                        'description': guideline['description'],
                        'last_completed': last_screening.date() if last_screening else None,
                        'next_due': self._calculate_next_due_date(guideline, last_screening),
                        'reasons': guideline.get('reasons', [])
                    }
                    
                    recommendations['screening_recommendations'].append(screening_rec)
                    
                    if guideline['priority'] == 'urgent':
                        recommendations['urgent_screenings'].append(screening_rec)
                    else:
                        recommendations['routine_screenings'].append(screening_rec)
            
            # Risk-based recommendations
            risk_factors = self._assess_risk_factors(user_id)
            if risk_factors:
                risk_based_recs = self._get_risk_based_recommendations(risk_factors, age)
                recommendations['screening_recommendations'].extend(risk_based_recs)
            
            # Lifestyle recommendations
            lifestyle_recs = self._get_lifestyle_recommendations(user_id, age)
            recommendations['lifestyle_recommendations'] = lifestyle_recs
            
            self.logger.info(f"Generated {len(recommendations['screening_recommendations'])} "
                           f"screening recommendations for user {user_id}")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting screening recommendations for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'success': False
            }
    
    def _get_age_based_guidelines(self, age: int) -> List[Dict[str, Any]]:
        """Get screening guidelines based on age."""
        guidelines = []
        
        # Cervical Cancer Screening
        if 21 <= age <= 65:
            guidelines.append({
                'type': 'cervical_cancer_screening',
                'frequency': 'every_3_years' if age < 30 else 'every_5_years',
                'priority': 'routine',
                'description': 'Pap smear for cervical cancer screening',
                'reasons': ['Prevent cervical cancer', 'Early detection of abnormal cells']
            })
        
        # Breast Cancer Screening
        if age >= 40:
            guidelines.append({
                'type': 'mammogram',
                'frequency': 'annually' if age >= 50 else 'every_2_years',
                'priority': 'routine',
                'description': 'Mammogram for breast cancer screening',
                'reasons': ['Early detection of breast cancer', 'Improved treatment outcomes']
            })
        
        # Bone Density Screening
        if age >= 65:
            guidelines.append({
                'type': 'bone_density_scan',
                'frequency': 'every_2_years',
                'priority': 'routine',
                'description': 'DEXA scan for osteoporosis screening',
                'reasons': ['Assess bone health', 'Prevent fractures']
            })
        
        # Cardiovascular Screening
        if age >= 35:
            guidelines.append({
                'type': 'lipid_panel',
                'frequency': 'every_5_years',
                'priority': 'routine',
                'description': 'Cholesterol and lipid screening',
                'reasons': ['Assess cardiovascular risk', 'Prevent heart disease']
            })
        
        # Blood Pressure Monitoring
        guidelines.append({
            'type': 'blood_pressure_check',
            'frequency': 'annually',
            'priority': 'routine',
            'description': 'Regular blood pressure monitoring',
            'reasons': ['Monitor cardiovascular health', 'Detect hypertension early']
        })
        
        # Diabetes Screening
        if age >= 35:
            guidelines.append({
                'type': 'diabetes_screening',
                'frequency': 'every_3_years',
                'priority': 'routine',
                'description': 'Blood glucose and HbA1c testing',
                'reasons': ['Early detection of diabetes', 'Prevent complications']
            })
        
        return guidelines
    
    def _get_last_screening(self, user_id: int, screening_type: str) -> Optional[datetime]:
        """Get the date of the last screening of specified type."""
        try:
            last_screening = HealthScreening.objects.filter(
                user_id=user_id,
                screening_type=screening_type
            ).order_by('-screening_date').first()
            
            return last_screening.screening_date if last_screening else None
            
        except Exception as e:
            self.logger.error(f"Error getting last screening for user {user_id}: {e}")
            return None
    
    def _is_screening_due(self, guideline: Dict[str, Any], last_screening: Optional[datetime]) -> bool:
        """Check if a screening is due based on guidelines and last screening date."""
        if not last_screening:
            return True
        
        frequency = guideline['frequency']
        frequency_mapping = {
            'annually': 365,
            'every_2_years': 730,
            'every_3_years': 1095,
            'every_5_years': 1825
        }
        
        days_since_last = (timezone.now().date() - last_screening.date()).days
        required_interval = frequency_mapping.get(frequency, 365)
        
        return days_since_last >= required_interval
    
    def _calculate_next_due_date(self, guideline: Dict[str, Any], last_screening: Optional[datetime]) -> str:
        """Calculate when the next screening is due."""
        if not last_screening:
            return timezone.now().date().isoformat()
        
        frequency = guideline['frequency']
        frequency_mapping = {
            'annually': 365,
            'every_2_years': 730,
            'every_3_years': 1095,
            'every_5_years': 1825
        }
        
        days_to_add = frequency_mapping.get(frequency, 365)
        next_due = last_screening.date() + timedelta(days=days_to_add)
        
        return next_due.isoformat()
    
    def _assess_risk_factors(self, user_id: int) -> List[str]:
        """Assess risk factors for additional screening recommendations."""
        risk_factors = []
        
        try:
            # Get user's medical history and family history
            # This would be expanded based on actual medical history model
            
            # Example risk factor assessment
            profile = WomensHealthProfile.objects.get(user_id=user_id)
            
            # Family history of breast cancer
            if hasattr(profile, 'family_history_breast_cancer') and profile.family_history_breast_cancer:
                risk_factors.append('family_history_breast_cancer')
            
            # History of PCOS
            if hasattr(profile, 'has_pcos') and profile.has_pcos:
                risk_factors.append('pcos')
            
            # Irregular cycles (potential hormone imbalance)
            cycles = profile.menstrualcycle_set.filter(
                cycle_start_date__gte=timezone.now().date() - timedelta(days=180)
            )
            
            if cycles.exists():
                cycle_lengths = [c.cycle_length for c in cycles if c.cycle_length]
                if cycle_lengths:
                    avg_length = sum(cycle_lengths) / len(cycle_lengths)
                    if avg_length < 21 or avg_length > 35:
                        risk_factors.append('irregular_cycles')
            
            return risk_factors
            
        except Exception as e:
            self.logger.error(f"Error assessing risk factors for user {user_id}: {e}")
            return []
    
    def _get_risk_based_recommendations(self, risk_factors: List[str], age: int) -> List[Dict[str, Any]]:
        """Get additional screening recommendations based on risk factors."""
        recommendations = []
        
        if 'family_history_breast_cancer' in risk_factors:
            if age >= 25:  # Earlier screening for high-risk individuals
                recommendations.append({
                    'screening_type': 'breast_mri',
                    'recommended_frequency': 'annually',
                    'priority': 'high',
                    'description': 'Annual breast MRI due to family history',
                    'last_completed': None,
                    'next_due': timezone.now().date().isoformat(),
                    'reasons': ['Family history of breast cancer', 'Enhanced early detection']
                })
        
        if 'pcos' in risk_factors:
            recommendations.append({
                'screening_type': 'diabetes_screening',
                'recommended_frequency': 'annually',
                'priority': 'high',
                'description': 'Annual diabetes screening due to PCOS',
                'last_completed': None,
                'next_due': timezone.now().date().isoformat(),
                'reasons': ['PCOS increases diabetes risk', 'Early intervention important']
            })
        
        if 'irregular_cycles' in risk_factors:
            recommendations.append({
                'screening_type': 'hormone_panel',
                'recommended_frequency': 'every_6_months',
                'priority': 'high',
                'description': 'Hormone panel due to irregular cycles',
                'last_completed': None,
                'next_due': timezone.now().date().isoformat(),
                'reasons': ['Irregular menstrual cycles', 'Hormone imbalance assessment']
            })
        
        return recommendations
    
    def _get_lifestyle_recommendations(self, user_id: int, age: int) -> List[Dict[str, Any]]:
        """Get lifestyle recommendations based on user data."""
        recommendations = []
        
        # General recommendations
        recommendations.extend([
            {
                'category': 'nutrition',
                'title': 'Calcium and Vitamin D',
                'description': 'Ensure adequate calcium (1000-1200mg) and vitamin D (600-800 IU) daily',
                'priority': 'medium',
                'reasons': ['Bone health', 'Hormonal balance']
            },
            {
                'category': 'exercise',
                'title': 'Regular Physical Activity',
                'description': '150 minutes of moderate aerobic activity per week',
                'priority': 'high',
                'reasons': ['Cardiovascular health', 'Mental wellbeing', 'Hormone regulation']
            },
            {
                'category': 'preventive_care',
                'title': 'Regular Self-Examinations',
                'description': 'Monthly breast self-examinations',
                'priority': 'high',
                'reasons': ['Early detection', 'Body awareness']
            }
        ])
        
        # Age-specific recommendations
        if age >= 40:
            recommendations.append({
                'category': 'nutrition',
                'title': 'Heart-Healthy Diet',
                'description': 'Focus on omega-3 fatty acids, fiber, and antioxidants',
                'priority': 'high',
                'reasons': ['Cardiovascular risk increases with age', 'Hormonal changes']
            })
        
        if age >= 50:
            recommendations.append({
                'category': 'lifestyle',
                'title': 'Stress Management',
                'description': 'Regular stress reduction practices (meditation, yoga, etc.)',
                'priority': 'high',
                'reasons': ['Menopause transition', 'Cardiovascular health']
            })
        
        return recommendations


class MedicalHistoryService:
    """Service for managing medical history and health records."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MedicalHistoryService")
    
    def initialize(self):
        """Initialize the medical history service."""
        self.logger.info("Medical History Service initialized")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'service': 'MedicalHistoryService',
            'status': 'active',
            'last_check': timezone.now().isoformat()
        }
    
    def update_medical_history(self, user_id: int, medical_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user's medical history with new information.
        
        Args:
            user_id: User ID
            medical_data: Medical history data to update
            
        Returns:
            Dictionary with update results
        """
        try:
            update_results = {
                'user_id': user_id,
                'updated_fields': [],
                'new_records_created': 0,
                'update_timestamp': timezone.now().isoformat()
            }
            
            # Get or create medical history record
            medical_history, created = MedicalHistory.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'created_at': timezone.now(),
                    'medical_conditions': [],
                    'medications': [],
                    'allergies': [],
                    'family_history': {},
                    'surgical_history': []
                }
            )
            
            if created:
                update_results['new_records_created'] = 1
            
            # Update medical conditions
            if 'medical_conditions' in medical_data:
                medical_history.medical_conditions = medical_data['medical_conditions']
                update_results['updated_fields'].append('medical_conditions')
            
            # Update medications
            if 'medications' in medical_data:
                medical_history.medications = medical_data['medications']
                update_results['updated_fields'].append('medications')
            
            # Update allergies
            if 'allergies' in medical_data:
                medical_history.allergies = medical_data['allergies']
                update_results['updated_fields'].append('allergies')
            
            # Update family history
            if 'family_history' in medical_data:
                medical_history.family_history = medical_data['family_history']
                update_results['updated_fields'].append('family_history')
            
            # Update surgical history
            if 'surgical_history' in medical_data:
                medical_history.surgical_history = medical_data['surgical_history']
                update_results['updated_fields'].append('surgical_history')
            
            medical_history.updated_at = timezone.now()
            medical_history.save()
            
            self.logger.info(f"Updated medical history for user {user_id}: "
                           f"{len(update_results['updated_fields'])} fields updated")
            
            return update_results
            
        except Exception as e:
            self.logger.error(f"Error updating medical history for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'success': False
            }
    
    def get_comprehensive_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive medical history summary.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with medical history summary
        """
        try:
            summary = {
                'user_id': user_id,
                'summary_generated': timezone.now().isoformat(),
                'medical_history': {},
                'recent_health_data': {},
                'health_trends': {},
                'risk_assessment': {}
            }
            
            # Get medical history
            try:
                medical_history = MedicalHistory.objects.get(user_id=user_id)
                summary['medical_history'] = {
                    'medical_conditions': medical_history.medical_conditions or [],
                    'medications': medical_history.medications or [],
                    'allergies': medical_history.allergies or [],
                    'family_history': medical_history.family_history or {},
                    'surgical_history': medical_history.surgical_history or [],
                    'last_updated': medical_history.updated_at.isoformat() if medical_history.updated_at else None
                }
            except MedicalHistory.DoesNotExist:
                summary['medical_history'] = {
                    'status': 'No medical history recorded',
                    'recommendation': 'Complete medical history for better health insights'
                }
            
            # Get recent health data
            profile = WomensHealthProfile.objects.get(user_id=user_id)
            
            # Recent cycles
            recent_cycles = profile.menstrualcycle_set.filter(
                cycle_start_date__gte=timezone.now().date() - timedelta(days=90)
            ).order_by('-cycle_start_date')[:3]
            
            summary['recent_health_data']['recent_cycles'] = [
                {
                    'start_date': cycle.cycle_start_date.isoformat(),
                    'length': cycle.cycle_length,
                    'flow_intensity': cycle.flow_intensity
                }
                for cycle in recent_cycles
            ]
            
            # Recent health logs
            recent_logs = profile.dailyhealthlog_set.filter(
                log_date__gte=timezone.now().date() - timedelta(days=30)
            ).order_by('-log_date')[:10]
            
            summary['recent_health_data']['recent_symptoms'] = [
                {
                    'date': log.log_date.isoformat(),
                    'mood': log.mood,
                    'energy_level': log.energy_level,
                    'symptoms': log.symptoms
                }
                for log in recent_logs
            ]
            
            # Generate health trends
            summary['health_trends'] = self._analyze_health_trends(user_id)
            
            # Generate risk assessment
            summary['risk_assessment'] = self._generate_risk_assessment(user_id)
            
            self.logger.info(f"Generated comprehensive medical summary for user {user_id}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating medical summary for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'success': False
            }
    
    def analyze_health_risks(self, user_id: int) -> Dict[str, Any]:
        """
        Analyze health risks based on medical history and current data.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with risk analysis
        """
        try:
            risk_analysis = {
                'user_id': user_id,
                'analysis_date': timezone.now().isoformat(),
                'risk_factors': [],
                'low_risk_areas': [],
                'recommendations': [],
                'overall_risk_score': 0
            }
            
            # Get medical history
            try:
                medical_history = MedicalHistory.objects.get(user_id=user_id)
                
                # Analyze medical conditions
                conditions = medical_history.medical_conditions or []
                high_risk_conditions = ['diabetes', 'hypertension', 'heart_disease', 'pcos']
                
                for condition in conditions:
                    if any(risk_condition in condition.lower() for risk_condition in high_risk_conditions):
                        risk_analysis['risk_factors'].append({
                            'category': 'medical_condition',
                            'factor': condition,
                            'risk_level': 'high',
                            'description': f'Existing medical condition: {condition}'
                        })
                
                # Analyze family history
                family_history = medical_history.family_history or {}
                for condition, relatives in family_history.items():
                    if relatives and condition.lower() in ['breast_cancer', 'ovarian_cancer', 'heart_disease']:
                        risk_analysis['risk_factors'].append({
                            'category': 'family_history',
                            'factor': condition,
                            'risk_level': 'moderate',
                            'description': f'Family history of {condition}'
                        })
                
            except MedicalHistory.DoesNotExist:
                risk_analysis['recommendations'].append({
                    'category': 'data_completion',
                    'recommendation': 'Complete medical history for accurate risk assessment',
                    'priority': 'high'
                })
            
            # Analyze cycle patterns for hormonal risks
            profile = WomensHealthProfile.objects.get(user_id=user_id)
            cycles = profile.menstrualcycle_set.filter(
                cycle_start_date__gte=timezone.now().date() - timedelta(days=180)
            )
            
            if cycles.exists():
                cycle_lengths = [c.cycle_length for c in cycles if c.cycle_length]
                if cycle_lengths:
                    avg_length = sum(cycle_lengths) / len(cycle_lengths)
                    if avg_length < 21 or avg_length > 35:
                        risk_analysis['risk_factors'].append({
                            'category': 'hormonal',
                            'factor': 'irregular_cycles',
                            'risk_level': 'moderate',
                            'description': 'Irregular menstrual cycles may indicate hormonal imbalance'
                        })
                    else:
                        risk_analysis['low_risk_areas'].append('regular_menstrual_cycles')
            
            # Calculate overall risk score
            high_risk_count = len([r for r in risk_analysis['risk_factors'] if r['risk_level'] == 'high'])
            moderate_risk_count = len([r for r in risk_analysis['risk_factors'] if r['risk_level'] == 'moderate'])
            
            risk_analysis['overall_risk_score'] = min(100, (high_risk_count * 30) + (moderate_risk_count * 15))
            
            # Generate recommendations based on risk factors
            if risk_analysis['overall_risk_score'] > 50:
                risk_analysis['recommendations'].append({
                    'category': 'medical_consultation',
                    'recommendation': 'Consult with healthcare provider for comprehensive risk assessment',
                    'priority': 'high'
                })
            
            self.logger.info(f"Completed health risk analysis for user {user_id}: "
                           f"Score {risk_analysis['overall_risk_score']}")
            
            return risk_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing health risks for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'success': False
            }
    
    def generate_health_report(self, user_id: int, report_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate health report for provider sharing.
        
        Args:
            user_id: User ID
            report_type: Type of report to generate
            
        Returns:
            Dictionary with generated report
        """
        try:
            report = {
                'user_id': user_id,
                'report_type': report_type,
                'generated_date': timezone.now().isoformat(),
                'report_sections': {},
                'summary': {},
                'recommendations': []
            }
            
            if report_type in ["comprehensive", "medical_history"]:
                # Medical history section
                try:
                    medical_history = MedicalHistory.objects.get(user_id=user_id)
                    report['report_sections']['medical_history'] = {
                        'medical_conditions': medical_history.medical_conditions or [],
                        'medications': medical_history.medications or [],
                        'allergies': medical_history.allergies or [],
                        'family_history': medical_history.family_history or {},
                        'surgical_history': medical_history.surgical_history or []
                    }
                except MedicalHistory.DoesNotExist:
                    report['report_sections']['medical_history'] = {'status': 'No recorded history'}
            
            if report_type in ["comprehensive", "menstrual_health"]:
                # Menstrual health section
                profile = WomensHealthProfile.objects.get(user_id=user_id)
                recent_cycles = profile.menstrualcycle_set.filter(
                    cycle_start_date__gte=timezone.now().date() - timedelta(days=365)
                ).order_by('-cycle_start_date')
                
                cycle_data = []
                for cycle in recent_cycles:
                    cycle_data.append({
                        'start_date': cycle.cycle_start_date.isoformat(),
                        'length': cycle.cycle_length,
                        'flow_intensity': cycle.flow_intensity,
                        'pain_level': cycle.pain_level
                    })
                
                report['report_sections']['menstrual_health'] = {
                    'cycle_count': len(cycle_data),
                    'cycles': cycle_data,
                    'average_cycle_length': sum(c['length'] for c in cycle_data if c['length']) / max(1, len([c for c in cycle_data if c['length']])) if cycle_data else None
                }
            
            if report_type in ["comprehensive", "symptoms_mood"]:
                # Symptoms and mood section
                profile = WomensHealthProfile.objects.get(user_id=user_id)
                recent_logs = profile.dailyhealthlog_set.filter(
                    log_date__gte=timezone.now().date() - timedelta(days=90)
                ).order_by('-log_date')
                
                symptoms_data = []
                for log in recent_logs:
                    symptoms_data.append({
                        'date': log.log_date.isoformat(),
                        'mood': log.mood,
                        'energy_level': log.energy_level,
                        'symptoms': log.symptoms,
                        'notes': log.notes
                    })
                
                report['report_sections']['symptoms_mood'] = {
                    'log_count': len(symptoms_data),
                    'recent_logs': symptoms_data
                }
            
            # Generate summary
            report['summary'] = {
                'report_completeness': self._calculate_report_completeness(report),
                'key_findings': self._extract_key_findings(report),
                'areas_needing_attention': self._identify_attention_areas(report)
            }
            
            self.logger.info(f"Generated {report_type} health report for user {user_id}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating health report for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'success': False
            }
    
    def track_medication_compliance(self, user_id: int) -> Dict[str, Any]:
        """Track medication compliance and adherence."""
        try:
            compliance_data = {
                'user_id': user_id,
                'tracking_date': timezone.now().isoformat(),
                'medications': [],
                'overall_compliance_score': 0,
                'recommendations': []
            }
            
            # Get current medications
            try:
                medical_history = MedicalHistory.objects.get(user_id=user_id)
                medications = medical_history.medications or []
                
                # For each medication, assess compliance
                # This would be expanded with actual medication tracking data
                for medication in medications:
                    med_compliance = {
                        'medication': medication.get('name', 'Unknown'),
                        'prescribed_frequency': medication.get('frequency', 'Unknown'),
                        'compliance_percentage': 85,  # Would calculate from actual tracking data
                        'missed_doses_week': 1,  # Would get from tracking data
                        'adherence_pattern': 'good'  # Would analyze from data
                    }
                    compliance_data['medications'].append(med_compliance)
                
                # Calculate overall compliance
                if compliance_data['medications']:
                    total_compliance = sum(med['compliance_percentage'] for med in compliance_data['medications'])
                    compliance_data['overall_compliance_score'] = total_compliance / len(compliance_data['medications'])
                
            except MedicalHistory.DoesNotExist:
                compliance_data['medications'] = []
                compliance_data['recommendations'].append({
                    'category': 'medication_setup',
                    'recommendation': 'Add medications to track compliance',
                    'priority': 'medium'
                })
            
            return compliance_data
            
        except Exception as e:
            self.logger.error(f"Error tracking medication compliance for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'success': False
            }
    
    def generate_clinical_insights(self, user_id: int) -> Dict[str, Any]:
        """Generate clinical insights based on health data patterns."""
        try:
            insights = {
                'user_id': user_id,
                'insights_generated': timezone.now().isoformat(),
                'clinical_insights': [],
                'pattern_analysis': {},
                'recommendations': []
            }
            
            # Analyze menstrual patterns
            profile = WomensHealthProfile.objects.get(user_id=user_id)
            cycles = profile.menstrualcycle_set.filter(
                cycle_start_date__gte=timezone.now().date() - timedelta(days=180)
            ).order_by('cycle_start_date')
            
            if cycles.count() >= 3:
                cycle_lengths = [c.cycle_length for c in cycles if c.cycle_length]
                
                if cycle_lengths:
                    avg_length = sum(cycle_lengths) / len(cycle_lengths)
                    std_deviation = (sum((x - avg_length) ** 2 for x in cycle_lengths) / len(cycle_lengths)) ** 0.5
                    
                    insights['pattern_analysis']['cycle_regularity'] = {
                        'average_length': round(avg_length, 1),
                        'variability': round(std_deviation, 1),
                        'regularity_assessment': 'regular' if std_deviation <= 5 else 'irregular'
                    }
                    
                    if std_deviation > 7:
                        insights['clinical_insights'].append({
                            'category': 'cycle_irregularity',
                            'finding': 'High cycle length variability detected',
                            'clinical_significance': 'May indicate hormonal imbalance',
                            'recommendation': 'Consider hormonal evaluation'
                        })
            
            # Analyze symptom patterns
            recent_logs = profile.dailyhealthlog_set.filter(
                log_date__gte=timezone.now().date() - timedelta(days=60)
            )
            
            if recent_logs.exists():
                # Mood pattern analysis
                mood_logs = [log.mood for log in recent_logs if log.mood]
                if mood_logs:
                    mood_variability = len(set(mood_logs)) / len(mood_logs)
                    insights['pattern_analysis']['mood_stability'] = {
                        'variability_score': round(mood_variability, 2),
                        'assessment': 'stable' if mood_variability < 0.6 else 'variable'
                    }
                    
                    if mood_variability > 0.8:
                        insights['clinical_insights'].append({
                            'category': 'mood_patterns',
                            'finding': 'High mood variability observed',
                            'clinical_significance': 'May correlate with hormonal fluctuations',
                            'recommendation': 'Track mood patterns in relation to cycle phases'
                        })
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating clinical insights for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'success': False
            }
    
    def _analyze_health_trends(self, user_id: int) -> Dict[str, Any]:
        """Analyze health trends over time."""
        trends = {}
        
        try:
            profile = WomensHealthProfile.objects.get(user_id=user_id)
            
            # Cycle length trends
            cycles = profile.menstrualcycle_set.filter(
                cycle_start_date__gte=timezone.now().date() - timedelta(days=365)
            ).order_by('cycle_start_date')
            
            if cycles.count() >= 6:
                recent_cycles = cycles.order_by('-cycle_start_date')[:3]
                older_cycles = cycles.order_by('-cycle_start_date')[3:6]
                
                recent_avg = sum(c.cycle_length for c in recent_cycles if c.cycle_length) / max(1, len([c for c in recent_cycles if c.cycle_length]))
                older_avg = sum(c.cycle_length for c in older_cycles if c.cycle_length) / max(1, len([c for c in older_cycles if c.cycle_length]))
                
                trends['cycle_length_trend'] = {
                    'direction': 'increasing' if recent_avg > older_avg else 'decreasing' if recent_avg < older_avg else 'stable',
                    'recent_average': round(recent_avg, 1),
                    'previous_average': round(older_avg, 1)
                }
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error analyzing health trends for user {user_id}: {e}")
            return {}
    
    def _generate_risk_assessment(self, user_id: int) -> Dict[str, Any]:
        """Generate basic risk assessment."""
        return {
            'cardiovascular_risk': 'low',  # Would be calculated based on various factors
            'reproductive_health_risk': 'low',
            'metabolic_risk': 'low',
            'overall_assessment': 'Low risk profile based on available data'
        }
    
    def _calculate_report_completeness(self, report: Dict[str, Any]) -> str:
        """Calculate how complete the health report is."""
        sections = report.get('report_sections', {})
        total_sections = 3  # medical_history, menstrual_health, symptoms_mood
        completed_sections = len([s for s in sections.values() if s and not s.get('status')])
        
        completeness = (completed_sections / total_sections) * 100
        
        if completeness >= 80:
            return 'comprehensive'
        elif completeness >= 60:
            return 'good'
        elif completeness >= 40:
            return 'moderate'
        else:
            return 'limited'
    
    def _extract_key_findings(self, report: Dict[str, Any]) -> List[str]:
        """Extract key findings from the report."""
        findings = []
        
        sections = report.get('report_sections', {})
        
        if 'menstrual_health' in sections:
            cycle_count = sections['menstrual_health'].get('cycle_count', 0)
            avg_length = sections['menstrual_health'].get('average_cycle_length')
            
            if cycle_count > 0:
                findings.append(f"Tracked {cycle_count} menstrual cycles")
                
                if avg_length:
                    if 21 <= avg_length <= 35:
                        findings.append(f"Regular cycle length (avg: {avg_length:.1f} days)")
                    else:
                        findings.append(f"Irregular cycle length (avg: {avg_length:.1f} days)")
        
        return findings
    
    def _identify_attention_areas(self, report: Dict[str, Any]) -> List[str]:
        """Identify areas that need medical attention."""
        attention_areas = []
        
        sections = report.get('report_sections', {})
        
        if 'medical_history' in sections and sections['medical_history'].get('status') == 'No recorded history':
            attention_areas.append("Medical history needs to be completed")
        
        if 'menstrual_health' in sections:
            avg_length = sections['menstrual_health'].get('average_cycle_length')
            if avg_length and (avg_length < 21 or avg_length > 35):
                attention_areas.append("Irregular menstrual cycles - consider medical evaluation")
        
        return attention_areas


class ProviderIntegrationService:
    """Service for healthcare provider integrations and appointment management."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ProviderIntegrationService")
    
    def initialize(self):
        """Initialize the provider integration service."""
        self.logger.info("Provider Integration Service initialized")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'service': 'ProviderIntegrationService',
            'status': 'active',
            'last_check': timezone.now().isoformat()
        }
    
    def schedule_appointment(self, user_id: int, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a medical appointment."""
        try:
            # Create appointment record
            appointment = Appointment.objects.create(
                user_id=user_id,
                appointment_type=appointment_data.get('type', 'general'),
                scheduled_date=appointment_data.get('date'),
                provider_name=appointment_data.get('provider', ''),
                notes=appointment_data.get('notes', ''),
                status='scheduled'
            )
            
            return {
                'appointment_id': appointment.id,
                'scheduled_date': appointment.scheduled_date.isoformat(),
                'provider': appointment.provider_name,
                'type': appointment.appointment_type,
                'status': 'successfully_scheduled'
            }
            
        except Exception as e:
            self.logger.error(f"Error scheduling appointment for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'success': False
            }
    
    def get_upcoming_appointments(self, user_id: int) -> Dict[str, Any]:
        """Get user's upcoming appointments."""
        try:
            upcoming_appointments = Appointment.objects.filter(
                user_id=user_id,
                scheduled_date__gte=timezone.now(),
                status__in=['scheduled', 'confirmed']
            ).order_by('scheduled_date')
            
            appointments_data = []
            for appointment in upcoming_appointments:
                appointments_data.append({
                    'id': appointment.id,
                    'type': appointment.appointment_type,
                    'date': appointment.scheduled_date.isoformat(),
                    'provider': appointment.provider_name,
                    'status': appointment.status,
                    'notes': appointment.notes
                })
            
            return {
                'user_id': user_id,
                'upcoming_appointments': appointments_data,
                'count': len(appointments_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting upcoming appointments for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'success': False
            }
    
    def connect_provider(self, user_id: int, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """Connect user with a healthcare provider."""
        try:
            # This would implement actual provider connection logic
            # For now, we'll simulate the connection
            
            connection_result = {
                'user_id': user_id,
                'provider_id': provider_data.get('provider_id'),
                'provider_name': provider_data.get('name', ''),
                'specialization': provider_data.get('specialization', ''),
                'connection_status': 'connected',
                'connected_at': timezone.now().isoformat()
            }
            
            return connection_result
            
        except Exception as e:
            self.logger.error(f"Error connecting provider for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'success': False
            }
    
    def sync_provider_data(self, user_id: int, provider_id: int) -> Dict[str, Any]:
        """Sync data with connected healthcare provider."""
        try:
            # This would implement actual data sync logic
            # For now, we'll simulate the sync
            
            sync_result = {
                'user_id': user_id,
                'provider_id': provider_id,
                'sync_status': 'completed',
                'last_sync': timezone.now().isoformat(),
                'records_synced': {
                    'appointments': 2,
                    'lab_results': 1,
                    'prescriptions': 0
                }
            }
            
            return sync_result
            
        except Exception as e:
            self.logger.error(f"Error syncing provider data for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'success': False
            }