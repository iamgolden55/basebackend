# api/tests/test_womens_health_models.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date, timedelta
import json

from api.models import (
    WomensHealthProfile,
    MenstrualCycle,
    PregnancyRecord,
    FertilityTracking,
    HealthGoal,
    DailyHealthLog,
    HealthScreening
)

User = get_user_model()


class CustomUserWomensHealthFieldsTestCase(TestCase):
    """Test CustomUser women's health verification fields"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_user_creation_default_values(self):
        """Test that users are created with proper default values for women's health fields"""
        self.assertFalse(self.user.womens_health_verified)
        self.assertIsNone(self.user.womens_health_verification_date)
        self.assertIsNone(self.user.womens_health_otp)
        self.assertIsNone(self.user.womens_health_otp_created_at)

    def test_womens_health_verification_flow(self):
        """Test the complete verification flow"""
        # Initially not verified
        self.assertFalse(self.user.womens_health_verified)
        
        # Set verification
        self.user.womens_health_verified = True
        self.user.womens_health_verification_date = timezone.now()
        self.user.save()
        
        # Check verification status
        self.assertTrue(self.user.womens_health_verified)
        self.assertIsNotNone(self.user.womens_health_verification_date)

    def test_otp_fields(self):
        """Test OTP generation and storage"""
        otp = "123456"
        otp_time = timezone.now()
        
        self.user.womens_health_otp = otp
        self.user.womens_health_otp_created_at = otp_time
        self.user.save()
        
        self.assertEqual(self.user.womens_health_otp, otp)
        self.assertEqual(self.user.womens_health_otp_created_at, otp_time)


class WomensHealthProfileTestCase(TestCase):
    """Test WomensHealthProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            date_of_birth=date(1990, 1, 1)
        )
        self.profile = WomensHealthProfile.objects.create(
            user=self.user,
            age_at_menarche=13,
            average_cycle_length=28,
            average_period_duration=5,
            pregnancy_status='not_pregnant',
            last_menstrual_period=date.today() - timedelta(days=15)
        )

    def test_profile_creation(self):
        """Test basic profile creation"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.average_cycle_length, 28)
        self.assertEqual(self.profile.pregnancy_status, 'not_pregnant')

    def test_one_to_one_relationship(self):
        """Test that each user can have only one women's health profile"""
        with self.assertRaises(IntegrityError):
            WomensHealthProfile.objects.create(
                user=self.user,
                average_cycle_length=30
            )

    def test_profile_completion_calculation(self):
        """Test profile completion percentage calculation"""
        # Initial profile should have some completion
        self.assertGreater(self.profile.profile_completion_percentage, 0)
        
        # Add more fields and check completion increases
        self.profile.current_contraception = 'oral_contraceptive'
        self.profile.primary_gynecologist = 'Dr. Smith'
        self.profile.exercise_frequency = 'weekly'
        self.profile.save()
        
        # Should increase completion percentage
        self.assertGreater(self.profile.profile_completion_percentage, 30)

    def test_current_cycle_day_calculation(self):
        """Test current cycle day calculation"""
        # Set LMP to 10 days ago
        self.profile.last_menstrual_period = date.today() - timedelta(days=10)
        self.profile.average_cycle_length = 28
        self.profile.save()
        
        # Should be day 11 of cycle
        self.assertEqual(self.profile.current_cycle_day, 11)

    def test_estimated_ovulation_date(self):
        """Test ovulation date estimation"""
        self.profile.last_menstrual_period = date.today() - timedelta(days=10)
        self.profile.average_cycle_length = 28
        self.profile.save()
        
        # Ovulation typically 14 days before next period
        expected_ovulation = self.profile.last_menstrual_period + timedelta(days=14)
        self.assertEqual(self.profile.estimated_ovulation_date, expected_ovulation)

    def test_estimated_next_period(self):
        """Test next period estimation"""
        lmp = date.today() - timedelta(days=10)
        self.profile.last_menstrual_period = lmp
        self.profile.average_cycle_length = 28
        self.profile.save()
        
        expected_next_period = lmp + timedelta(days=28)
        self.assertEqual(self.profile.estimated_next_period, expected_next_period)

    def test_pregnancy_status_properties(self):
        """Test pregnancy status helper properties"""
        # Test not pregnant
        self.profile.pregnancy_status = 'not_pregnant'
        self.profile.save()
        self.assertFalse(self.profile.is_pregnant)
        self.assertFalse(self.profile.is_trying_to_conceive)
        
        # Test pregnant
        self.profile.pregnancy_status = 'pregnant'
        self.profile.save()
        self.assertTrue(self.profile.is_pregnant)
        self.assertFalse(self.profile.is_trying_to_conceive)
        
        # Test trying to conceive
        self.profile.pregnancy_status = 'trying_to_conceive'
        self.profile.save()
        self.assertFalse(self.profile.is_pregnant)
        self.assertTrue(self.profile.is_trying_to_conceive)

    def test_fertility_tracking_needs(self):
        """Test fertility tracking needs assessment"""
        # Enable fertility tracking for not pregnant user
        self.profile.pregnancy_status = 'not_pregnant'
        self.profile.fertility_tracking_enabled = True
        self.profile.save()
        self.assertTrue(self.profile.needs_fertility_tracking)
        
        # Disable fertility tracking
        self.profile.fertility_tracking_enabled = False
        self.profile.save()
        self.assertFalse(self.profile.needs_fertility_tracking)
        
        # Pregnant users don't need fertility tracking
        self.profile.pregnancy_status = 'pregnant'
        self.profile.fertility_tracking_enabled = True
        self.profile.save()
        self.assertFalse(self.profile.needs_fertility_tracking)

    def test_health_conditions_retrieval(self):
        """Test health conditions compilation"""
        # No conditions initially
        conditions = self.profile.get_health_conditions()
        self.assertEqual(conditions, ['None reported'])
        
        # Add some conditions
        self.profile.pcos = True
        self.profile.endometriosis = True
        self.profile.save()
        
        conditions = self.profile.get_health_conditions()
        self.assertIn('PCOS', conditions)
        self.assertIn('Endometriosis', conditions)

    def test_fertility_window_calculation(self):
        """Test fertile window calculation"""
        self.profile.last_menstrual_period = date.today() - timedelta(days=10)
        self.profile.average_cycle_length = 28
        self.profile.save()
        
        fertility_window = self.profile.get_fertility_window()
        self.assertIsNotNone(fertility_window)
        self.assertIn('start', fertility_window)
        self.assertIn('end', fertility_window)
        self.assertIn('ovulation', fertility_window)

    def test_health_summary(self):
        """Test health summary generation"""
        summary = self.profile.get_health_summary()
        self.assertIn('pregnancy_status', summary)
        self.assertIn('cycle_length', summary)
        self.assertIn('contraception', summary)
        self.assertIn('profile_completion', summary)


class MenstrualCycleTestCase(TestCase):
    """Test MenstrualCycle model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.profile = WomensHealthProfile.objects.create(
            user=self.user,
            average_cycle_length=28
        )
        self.cycle = MenstrualCycle.objects.create(
            womens_health_profile=self.profile,
            cycle_start_date=date.today() - timedelta(days=10),
            period_end_date=date.today() - timedelta(days=6),
            flow_intensity='medium',
            is_current_cycle=True
        )

    def test_cycle_creation(self):
        """Test basic cycle creation"""
        self.assertEqual(self.cycle.womens_health_profile, self.profile)
        self.assertEqual(self.cycle.flow_intensity, 'medium')
        self.assertTrue(self.cycle.is_current_cycle)

    def test_cycle_length_calculation(self):
        """Test automatic cycle length calculation"""
        cycle_end = self.cycle.cycle_start_date + timedelta(days=27)
        self.cycle.cycle_end_date = cycle_end
        self.cycle.save()
        
        # Should calculate 28 days (inclusive)
        self.assertEqual(self.cycle.cycle_length, 28)

    def test_period_length_calculation(self):
        """Test automatic period length calculation"""
        # Period end is 4 days after start
        expected_length = (self.cycle.period_end_date - self.cycle.cycle_start_date).days + 1
        self.cycle.save()
        
        self.assertEqual(self.cycle.period_length, expected_length)

    def test_current_cycle_day(self):
        """Test current cycle day calculation"""
        # Cycle started 10 days ago, so should be day 11
        self.assertEqual(self.cycle.cycle_day, 11)

    def test_single_current_cycle_constraint(self):
        """Test that only one cycle can be current per profile"""
        # Create another cycle
        new_cycle = MenstrualCycle.objects.create(
            womens_health_profile=self.profile,
            cycle_start_date=date.today() - timedelta(days=38),
            is_current_cycle=True
        )
        
        # Refresh the original cycle
        self.cycle.refresh_from_db()
        
        # Original cycle should no longer be current
        self.assertFalse(self.cycle.is_current_cycle)
        self.assertTrue(new_cycle.is_current_cycle)

    def test_cycle_phase_detection(self):
        """Test cycle phase detection"""
        # Should be in follicular phase (day 11 of 28-day cycle)
        phase_info = self.cycle.cycle_phase
        self.assertIsNotNone(phase_info)
        self.assertIn('phase', phase_info)
        
    def test_fertile_window_detection(self):
        """Test fertile window detection"""
        # Add ovulation date
        self.cycle.ovulation_date = date.today() - timedelta(days=2)
        self.cycle.save()
        
        # Should be in fertile window (within 5 days of ovulation)
        self.assertTrue(self.cycle.is_in_fertile_window)

    def test_fertility_status(self):
        """Test fertility status assessment"""
        self.cycle.ovulation_date = date.today() + timedelta(days=3)
        self.cycle.save()
        
        fertility_status = self.cycle.get_fertility_status()
        self.assertIn('status', fertility_status)
        self.assertIn('message', fertility_status)

    def test_data_completeness_calculation(self):
        """Test data completeness scoring"""
        # Should have some completeness initially
        self.assertGreater(self.cycle.data_completeness_score, 0)
        
        # Add more data
        self.cycle.ovulation_date = date.today() - timedelta(days=2)
        self.cycle.cycle_quality_score = 8
        self.cycle.stress_level = 'moderate'
        self.cycle.save()
        
        # Should increase completeness
        self.assertGreater(self.cycle.data_completeness_score, 40)

    def test_cycle_summary(self):
        """Test cycle summary generation"""
        summary = self.cycle.get_summary()
        self.assertIn('cycle_start', summary)
        self.assertIn('flow_intensity', summary)
        self.assertIn('is_current', summary)
        self.assertIn('fertility_status', summary)


class PregnancyRecordTestCase(TestCase):
    """Test PregnancyRecord model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            date_of_birth=date(1990, 1, 1)
        )
        self.profile = WomensHealthProfile.objects.create(
            user=self.user,
            pregnancy_status='pregnant'
        )
        self.pregnancy = PregnancyRecord.objects.create(
            womens_health_profile=self.profile,
            last_menstrual_period=date.today() - timedelta(days=70),
            pregnancy_start_date=date.today() - timedelta(days=60),
            pregnancy_status='ongoing',
            is_current_pregnancy=True
        )

    def test_pregnancy_creation(self):
        """Test basic pregnancy record creation"""
        self.assertEqual(self.pregnancy.womens_health_profile, self.profile)
        self.assertEqual(self.pregnancy.pregnancy_status, 'ongoing')
        self.assertTrue(self.pregnancy.is_current_pregnancy)

    def test_pregnancy_number_auto_increment(self):
        """Test automatic pregnancy number assignment"""
        # First pregnancy should be number 1
        self.assertEqual(self.pregnancy.pregnancy_number, 1)
        
        # Create second pregnancy
        second_pregnancy = PregnancyRecord.objects.create(
            womens_health_profile=self.profile,
            last_menstrual_period=date.today() - timedelta(days=365),
            pregnancy_start_date=date.today() - timedelta(days=355),
            pregnancy_status='completed_delivery'
        )
        
        # Should be number 2
        self.assertEqual(second_pregnancy.pregnancy_number, 2)

    def test_single_current_pregnancy_constraint(self):
        """Test that only one pregnancy can be current per profile"""
        # Create another current pregnancy
        new_pregnancy = PregnancyRecord.objects.create(
            womens_health_profile=self.profile,
            last_menstrual_period=date.today() - timedelta(days=30),
            pregnancy_start_date=date.today() - timedelta(days=20),
            is_current_pregnancy=True
        )
        
        # Refresh original pregnancy
        self.pregnancy.refresh_from_db()
        
        # Original should no longer be current
        self.assertFalse(self.pregnancy.is_current_pregnancy)
        self.assertTrue(new_pregnancy.is_current_pregnancy)

    def test_gestational_age_calculation(self):
        """Test gestational age calculation"""
        gestational_age = self.pregnancy.current_gestational_age
        self.assertIsNotNone(gestational_age)
        self.assertIn('weeks', gestational_age)
        self.assertIn('days', gestational_age)
        self.assertGreater(gestational_age['weeks'], 8)  # Should be around 10 weeks

    def test_trimester_calculation(self):
        """Test trimester determination"""
        trimester = self.pregnancy.trimester
        self.assertIsNotNone(trimester)
        self.assertIn('number', trimester)
        self.assertEqual(trimester['number'], 1)  # Should be first trimester

    def test_due_date_auto_calculation(self):
        """Test automatic due date calculation"""
        # Should calculate due date 280 days from LMP
        expected_due_date = self.pregnancy.last_menstrual_period + timedelta(days=280)
        self.assertEqual(self.pregnancy.estimated_due_date, expected_due_date)

    def test_conception_date_auto_calculation(self):
        """Test automatic conception date calculation"""
        # Should calculate conception date 14 days after LMP
        expected_conception = self.pregnancy.last_menstrual_period + timedelta(days=14)
        self.assertEqual(self.pregnancy.conception_date, expected_conception)

    def test_days_until_due_date(self):
        """Test days until due date calculation"""
        days_until_due = self.pregnancy.days_until_due_date
        self.assertIsNotNone(days_until_due)
        self.assertGreater(days_until_due, 200)  # Should be around 210 days

    def test_high_risk_assessment(self):
        """Test high risk pregnancy assessment"""
        # Initially should not be high risk
        self.assertFalse(self.pregnancy.is_high_risk)
        
        # Add risk factors
        self.pregnancy.risk_level = 'high'
        self.pregnancy.risk_factors = ['gestational_diabetes', 'advanced_maternal_age', 'previous_preterm_birth']
        self.pregnancy.save()
        
        # Should now be high risk
        self.assertTrue(self.pregnancy.is_high_risk)

    def test_pregnancy_summary(self):
        """Test pregnancy summary generation"""
        summary = self.pregnancy.get_pregnancy_summary()
        self.assertIn('pregnancy_number', summary)
        self.assertIn('status', summary)
        self.assertIn('is_current', summary)
        self.assertIn('gestational_age', summary)
        self.assertIn('trimester', summary)


class FertilityTrackingTestCase(TestCase):
    """Test FertilityTracking model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.profile = WomensHealthProfile.objects.create(
            user=self.user,
            fertility_tracking_enabled=True
        )
        self.tracking = FertilityTracking.objects.create(
            womens_health_profile=self.profile,
            date=date.today(),
            cycle_day=14,
            basal_body_temperature=36.8,
            cervical_mucus_type='egg_white',
            ovulation_test_result='positive'
        )

    def test_tracking_creation(self):
        """Test basic fertility tracking creation"""
        self.assertEqual(self.tracking.womens_health_profile, self.profile)
        self.assertEqual(self.tracking.cycle_day, 14)
        self.assertEqual(self.tracking.cervical_mucus_type, 'egg_white')

    def test_unique_constraint_per_date(self):
        """Test that only one tracking entry per date per profile"""
        with self.assertRaises(IntegrityError):
            FertilityTracking.objects.create(
                womens_health_profile=self.profile,
                date=date.today(),  # Same date
                cycle_day=15
            )

    def test_fertility_score_calculation(self):
        """Test fertility score calculation"""
        fertility_score = self.tracking.fertility_score
        self.assertGreaterEqual(fertility_score, 0)
        self.assertLessEqual(fertility_score, 10)
        
        # Should have high score due to egg white mucus and positive OPK
        self.assertGreater(fertility_score, 6)

    def test_ovulation_day_detection(self):
        """Test potential ovulation day detection"""
        # Should detect as potential ovulation day
        self.assertTrue(self.tracking.is_potential_ovulation_day)

    def test_fertile_window_status(self):
        """Test fertile window status assessment"""
        status = self.tracking.get_fertile_window_status()
        self.assertIn('status', status)
        self.assertEqual(status['status'], 'peak_fertility')

    def test_data_completeness_scoring(self):
        """Test data completeness scoring"""
        # Should have good completeness with current data
        self.assertGreater(self.tracking.data_completeness_score, 50)
        
        # Add more data
        self.tracking.symptoms = ['ovulation_pain', 'breast_tenderness']
        self.tracking.stress_level = 'low'
        self.tracking.sleep_quality = 'good'
        self.tracking.save()
        
        # Should increase completeness
        self.assertGreater(self.tracking.data_completeness_score, 70)

    def test_tracking_summary(self):
        """Test tracking summary generation"""
        summary = self.tracking.get_summary()
        self.assertIn('date', summary)
        self.assertIn('fertility_score', summary)
        self.assertIn('fertile_window_status', summary)
        self.assertIn('potential_ovulation', summary)


class HealthGoalTestCase(TestCase):
    """Test HealthGoal model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.profile = WomensHealthProfile.objects.create(user=self.user)
        self.goal = HealthGoal.objects.create(
            womens_health_profile=self.profile,
            title='Drink 8 glasses of water daily',
            category='hydration',
            goal_type='numeric',
            target_value=8,
            unit_of_measurement='glasses',
            target_date=date.today() + timedelta(days=30)
        )

    def test_goal_creation(self):
        """Test basic goal creation"""
        self.assertEqual(self.goal.title, 'Drink 8 glasses of water daily')
        self.assertEqual(self.goal.category, 'hydration')
        self.assertEqual(self.goal.target_value, 8)

    def test_progress_calculation(self):
        """Test progress percentage calculation"""
        # Update progress
        self.goal.current_value = 4  # 50% progress
        self.goal.save()
        
        self.assertEqual(self.goal.progress_percentage, 50)

    def test_goal_completion(self):
        """Test goal completion detection"""
        # Complete the goal
        self.goal.current_value = 8
        self.goal.save()
        
        self.assertEqual(self.goal.progress_percentage, 100)
        self.assertEqual(self.goal.status, 'completed')
        self.assertIsNotNone(self.goal.completed_date)

    def test_streak_tracking(self):
        """Test streak tracking functionality"""
        # Simulate progress updates
        self.goal.update_progress(2, "Good start")
        self.assertEqual(self.goal.current_streak, 1)
        
        # Update next day
        self.goal.last_activity_date = date.today() - timedelta(days=1)
        self.goal.update_progress(3, "Continuing")
        self.assertEqual(self.goal.current_streak, 2)

    def test_overdue_detection(self):
        """Test overdue goal detection"""
        # Set target date in the past
        self.goal.target_date = date.today() - timedelta(days=1)
        self.goal.save()
        
        self.assertTrue(self.goal.is_overdue)

    def test_days_calculations(self):
        """Test days since start and until target calculations"""
        days_since_start = self.goal.days_since_start
        days_until_target = self.goal.days_until_target
        
        self.assertGreaterEqual(days_since_start, 0)
        self.assertEqual(days_until_target, 30)

    def test_goal_reset(self):
        """Test goal reset functionality"""
        # Make some progress
        self.goal.current_value = 5
        self.goal.current_streak = 3
        self.goal.save()
        
        # Reset goal
        self.goal.reset_goal()
        
        self.assertEqual(self.goal.current_value, 0)
        self.assertEqual(self.goal.current_streak, 0)
        self.assertEqual(self.goal.status, 'active')

    def test_goal_summary(self):
        """Test goal summary generation"""
        summary = self.goal.get_goal_summary()
        self.assertIn('title', summary)
        self.assertIn('progress_percentage', summary)
        self.assertIn('current_streak', summary)
        self.assertIn('days_until_target', summary)


class DailyHealthLogTestCase(TestCase):
    """Test DailyHealthLog model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.profile = WomensHealthProfile.objects.create(user=self.user)
        self.log = DailyHealthLog.objects.create(
            womens_health_profile=self.profile,
            date=date.today(),
            mood='good',
            energy_level='high',
            sleep_duration_hours=8.0,
            sleep_quality='good',
            exercise_performed=True,
            water_intake_liters=2.5
        )

    def test_log_creation(self):
        """Test basic log creation"""
        self.assertEqual(self.log.womens_health_profile, self.profile)
        self.assertEqual(self.log.mood, 'good')
        self.assertEqual(self.log.sleep_duration_hours, 8.0)

    def test_unique_constraint_per_date(self):
        """Test that only one log per date per profile"""
        with self.assertRaises(IntegrityError):
            DailyHealthLog.objects.create(
                womens_health_profile=self.profile,
                date=date.today(),  # Same date
                mood='excellent'
            )

    def test_health_score_calculation(self):
        """Test health score calculation"""
        health_score = self.log.health_score
        self.assertGreaterEqual(health_score, 0)
        self.assertLessEqual(health_score, 10)
        
        # Should have good score with positive inputs
        self.assertGreater(health_score, 6)

    def test_data_completeness_calculation(self):
        """Test data completeness calculation"""
        # Should have good completeness with current data
        self.assertGreater(self.log.data_completeness_score, 40)
        
        # Add more data
        self.log.steps_count = 10000
        self.log.emotional_wellbeing_score = 8
        self.log.self_care_activities = ['meditation', 'reading']
        self.log.save()
        
        # Should increase completeness
        self.assertGreater(self.log.data_completeness_score, 60)

    def test_weekly_trends(self):
        """Test weekly trends calculation"""
        # Create additional logs for the week
        for i in range(1, 7):
            DailyHealthLog.objects.create(
                womens_health_profile=self.profile,
                date=date.today() - timedelta(days=i),
                mood='good',
                energy_level='normal',
                exercise_performed=True if i % 2 == 0 else False
            )
        
        trends = self.log.get_weekly_trends()
        self.assertIn('exercise_days', trends)
        self.assertIn('average_health_score', trends)
        self.assertGreater(trends['exercise_days'], 0)

    def test_log_summary(self):
        """Test log summary generation"""
        summary = self.log.get_summary()
        self.assertIn('date', summary)
        self.assertIn('health_score', summary)
        self.assertIn('mental_health', summary)
        self.assertIn('exercise', summary)


class HealthScreeningTestCase(TestCase):
    """Test HealthScreening model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            date_of_birth=date(1985, 1, 1)
        )
        self.profile = WomensHealthProfile.objects.create(user=self.user)
        self.screening = HealthScreening.objects.create(
            womens_health_profile=self.profile,
            screening_type='pap_smear',
            scheduled_date=date.today() + timedelta(days=30),
            provider_name='Dr. Smith',
            recommended_frequency_months=36
        )

    def test_screening_creation(self):
        """Test basic screening creation"""
        self.assertEqual(self.screening.womens_health_profile, self.profile)
        self.assertEqual(self.screening.screening_type, 'pap_smear')
        self.assertEqual(self.screening.status, 'scheduled')

    def test_status_updates(self):
        """Test automatic status updates"""
        # Complete the screening
        self.screening.completed_date = date.today()
        self.screening.result_status = 'normal'
        self.screening.save()
        
        self.assertEqual(self.screening.status, 'completed')

    def test_next_due_date_calculation(self):
        """Test automatic next due date calculation"""
        # Complete screening
        self.screening.completed_date = date.today()
        self.screening.save()
        
        # Should calculate next due date
        expected_next_due = date.today() + timedelta(days=36*30)  # Approximately 36 months
        self.assertAlmostEqual(
            self.screening.next_due_date,
            expected_next_due,
            delta=timedelta(days=5)  # Allow some variance
        )

    def test_age_calculation(self):
        """Test age at screening calculation"""
        self.screening.scheduled_date = date.today()
        self.screening.save()
        
        # Should calculate age (approximately 40 years old)
        self.assertGreater(self.screening.age_at_screening, 35)
        self.assertLess(self.screening.age_at_screening, 45)

    def test_due_soon_detection(self):
        """Test due soon detection"""
        # Set next due date to near future
        self.screening.next_due_date = date.today() + timedelta(days=20)
        self.screening.save()
        
        self.assertTrue(self.screening.is_due_soon(days_ahead=30))
        self.assertFalse(self.screening.is_due_soon(days_ahead=15))

    def test_days_calculations(self):
        """Test days until due and since last calculations"""
        self.screening.next_due_date = date.today() + timedelta(days=30)
        self.screening.completed_date = date.today() - timedelta(days=365)
        self.screening.save()
        
        self.assertEqual(self.screening.days_until_due(), 30)
        self.assertEqual(self.screening.days_since_last(), 365)

    def test_screening_summary(self):
        """Test screening summary generation"""
        summary = self.screening.get_summary()
        self.assertIn('screening_type', summary)
        self.assertIn('status', summary)
        self.assertIn('days_until_due', summary)
        self.assertIn('is_due_soon', summary)


class ModelIntegrationTestCase(TestCase):
    """Test integration between women's health models"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.profile = WomensHealthProfile.objects.create(
            user=self.user,
            fertility_tracking_enabled=True
        )

    def test_profile_to_cycle_relationship(self):
        """Test relationship between profile and cycles"""
        # Create multiple cycles
        cycle1 = MenstrualCycle.objects.create(
            womens_health_profile=self.profile,
            cycle_start_date=date.today() - timedelta(days=56),
            cycle_length=28
        )
        cycle2 = MenstrualCycle.objects.create(
            womens_health_profile=self.profile,
            cycle_start_date=date.today() - timedelta(days=28),
            is_current_cycle=True
        )
        
        # Test reverse relationship
        cycles = self.profile.menstrual_cycles.all()
        self.assertEqual(cycles.count(), 2)
        self.assertIn(cycle1, cycles)
        self.assertIn(cycle2, cycles)

    def test_goal_progress_in_daily_log(self):
        """Test goal progress tracking in daily health logs"""
        # Create a goal
        goal = HealthGoal.objects.create(
            womens_health_profile=self.profile,
            title='Daily water intake',
            goal_type='numeric',
            target_value=8
        )
        
        # Create daily log with goal progress
        daily_log = DailyHealthLog.objects.create(
            womens_health_profile=self.profile,
            date=date.today(),
            goal_progress={
                str(goal.id): {
                    'goal_title': goal.title,
                    'progress_value': 6,
                    'notes': 'Good progress today'
                }
            }
        )
        
        # Verify goal progress is stored
        self.assertIn(str(goal.id), daily_log.goal_progress)

    def test_fertility_tracking_with_cycles(self):
        """Test fertility tracking integration with cycles"""
        # Create current cycle
        cycle = MenstrualCycle.objects.create(
            womens_health_profile=self.profile,
            cycle_start_date=date.today() - timedelta(days=14),
            is_current_cycle=True
        )
        
        # Create fertility tracking for cycle day
        tracking = FertilityTracking.objects.create(
            womens_health_profile=self.profile,
            date=date.today(),
            cycle_day=15,
            ovulation_test_result='positive'
        )
        
        # Both should reference the same profile
        self.assertEqual(tracking.womens_health_profile, cycle.womens_health_profile)

    def test_cascade_deletion(self):
        """Test cascade deletion when profile is deleted"""
        # Create related objects
        cycle = MenstrualCycle.objects.create(
            womens_health_profile=self.profile,
            cycle_start_date=date.today()
        )
        goal = HealthGoal.objects.create(
            womens_health_profile=self.profile,
            title='Test goal',
            goal_type='boolean'
        )
        tracking = FertilityTracking.objects.create(
            womens_health_profile=self.profile,
            date=date.today()
        )
        
        # Delete profile
        profile_id = self.profile.id
        self.profile.delete()
        
        # Related objects should be deleted
        self.assertFalse(MenstrualCycle.objects.filter(womens_health_profile_id=profile_id).exists())
        self.assertFalse(HealthGoal.objects.filter(womens_health_profile_id=profile_id).exists())
        self.assertFalse(FertilityTracking.objects.filter(womens_health_profile_id=profile_id).exists())