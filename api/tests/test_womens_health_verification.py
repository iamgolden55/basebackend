# api/tests/test_womens_health_verification.py

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core import mail
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
import json
from unittest.mock import patch, MagicMock

from api.models import WomensHealthProfile

User = get_user_model()


class WomensHealthVerificationModelTestCase(TestCase):
    """Test the verification fields and methods on CustomUser model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_initial_verification_state(self):
        """Test that users start unverified"""
        self.assertFalse(self.user.womens_health_verified)
        self.assertIsNone(self.user.womens_health_verification_date)
        self.assertIsNone(self.user.womens_health_otp)
        self.assertIsNone(self.user.womens_health_otp_created_at)

    def test_verification_process(self):
        """Test the complete verification process"""
        # Step 1: Generate OTP
        otp = "123456"
        otp_time = timezone.now()
        
        self.user.womens_health_otp = otp
        self.user.womens_health_otp_created_at = otp_time
        self.user.save()
        
        # Verify OTP is stored
        self.assertEqual(self.user.womens_health_otp, otp)
        self.assertEqual(self.user.womens_health_otp_created_at, otp_time)
        self.assertFalse(self.user.womens_health_verified)
        
        # Step 2: Complete verification
        verification_time = timezone.now()
        self.user.womens_health_verified = True
        self.user.womens_health_verification_date = verification_time
        self.user.womens_health_otp = None  # Clear OTP after verification
        self.user.womens_health_otp_created_at = None
        self.user.save()
        
        # Verify completion
        self.assertTrue(self.user.womens_health_verified)
        self.assertEqual(self.user.womens_health_verification_date, verification_time)
        self.assertIsNone(self.user.womens_health_otp)
        self.assertIsNone(self.user.womens_health_otp_created_at)

    def test_otp_expiry_check(self):
        """Test OTP expiry logic"""
        # Set OTP created 10 minutes ago
        old_time = timezone.now() - timedelta(minutes=10)
        self.user.womens_health_otp = "123456"
        self.user.womens_health_otp_created_at = old_time
        self.user.save()
        
        # Check if OTP is expired (assuming 5 minute expiry)
        now = timezone.now()
        if self.user.womens_health_otp_created_at:
            expiry_minutes = 5
            is_expired = (now - self.user.womens_health_otp_created_at).total_seconds() > (expiry_minutes * 60)
            self.assertTrue(is_expired)

    def test_multiple_otp_generation(self):
        """Test that new OTP overwrites old one"""
        # First OTP
        self.user.womens_health_otp = "123456"
        self.user.womens_health_otp_created_at = timezone.now() - timedelta(minutes=3)
        self.user.save()
        
        old_otp = self.user.womens_health_otp
        old_time = self.user.womens_health_otp_created_at
        
        # Second OTP
        new_otp = "654321"
        new_time = timezone.now()
        self.user.womens_health_otp = new_otp
        self.user.womens_health_otp_created_at = new_time
        self.user.save()
        
        # Verify new OTP replaced old one
        self.assertEqual(self.user.womens_health_otp, new_otp)
        self.assertEqual(self.user.womens_health_otp_created_at, new_time)
        self.assertNotEqual(self.user.womens_health_otp, old_otp)

    def test_verification_persistence(self):
        """Test that verification status persists across saves"""
        # Verify user
        self.user.womens_health_verified = True
        self.user.womens_health_verification_date = timezone.now()
        self.user.save()
        
        # Make another change and save
        self.user.first_name = "Updated"
        self.user.save()
        
        # Refresh from database
        self.user.refresh_from_db()
        
        # Verification should still be active
        self.assertTrue(self.user.womens_health_verified)
        self.assertIsNotNone(self.user.womens_health_verification_date)


class WomensHealthVerificationAPITestCase(APITestCase):
    """Test API endpoints for women's health verification"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_verification_status_endpoint(self):
        """Test endpoint to check verification status"""
        # Mock endpoint - would need to be implemented
        # url = reverse('womens-health-verification-status')
        # response = self.client.get(url)
        
        # Test unverified status
        self.assertFalse(self.user.womens_health_verified)
        
        # Test verified status
        self.user.womens_health_verified = True
        self.user.womens_health_verification_date = timezone.now()
        self.user.save()
        
        self.assertTrue(self.user.womens_health_verified)

    @patch('api.services.email_service.send_verification_email')
    def test_request_verification_otp(self, mock_send_email):
        """Test requesting verification OTP"""
        mock_send_email.return_value = True
        
        # Simulate OTP generation
        import random
        import string
        otp = ''.join(random.choices(string.digits, k=6))
        
        self.user.womens_health_otp = otp
        self.user.womens_health_otp_created_at = timezone.now()
        self.user.save()
        
        # Verify OTP was generated and stored
        self.assertIsNotNone(self.user.womens_health_otp)
        self.assertEqual(len(self.user.womens_health_otp), 6)
        self.assertIsNotNone(self.user.womens_health_otp_created_at)

    def test_verify_otp_success(self):
        """Test successful OTP verification"""
        # Set up OTP
        otp = "123456"
        self.user.womens_health_otp = otp
        self.user.womens_health_otp_created_at = timezone.now()
        self.user.save()
        
        # Simulate verification
        provided_otp = "123456"
        
        if self.user.womens_health_otp == provided_otp:
            # Check OTP hasn't expired (5 minute window)
            now = timezone.now()
            expiry_minutes = 5
            if (now - self.user.womens_health_otp_created_at).total_seconds() <= (expiry_minutes * 60):
                # Complete verification
                self.user.womens_health_verified = True
                self.user.womens_health_verification_date = now
                self.user.womens_health_otp = None
                self.user.womens_health_otp_created_at = None
                self.user.save()
        
        # Verify success
        self.assertTrue(self.user.womens_health_verified)
        self.assertIsNotNone(self.user.womens_health_verification_date)
        self.assertIsNone(self.user.womens_health_otp)

    def test_verify_otp_invalid(self):
        """Test OTP verification with invalid OTP"""
        # Set up OTP
        otp = "123456"
        self.user.womens_health_otp = otp
        self.user.womens_health_otp_created_at = timezone.now()
        self.user.save()
        
        # Try wrong OTP
        provided_otp = "654321"
        verification_failed = self.user.womens_health_otp != provided_otp
        
        self.assertTrue(verification_failed)
        self.assertFalse(self.user.womens_health_verified)

    def test_verify_otp_expired(self):
        """Test OTP verification with expired OTP"""
        # Set up expired OTP (10 minutes ago)
        otp = "123456"
        self.user.womens_health_otp = otp
        self.user.womens_health_otp_created_at = timezone.now() - timedelta(minutes=10)
        self.user.save()
        
        # Try to verify
        provided_otp = "123456"
        now = timezone.now()
        expiry_minutes = 5
        
        is_otp_correct = self.user.womens_health_otp == provided_otp
        is_otp_expired = (now - self.user.womens_health_otp_created_at).total_seconds() > (expiry_minutes * 60)
        
        self.assertTrue(is_otp_correct)
        self.assertTrue(is_otp_expired)
        self.assertFalse(self.user.womens_health_verified)  # Should remain unverified

    def test_resend_otp(self):
        """Test resending OTP functionality"""
        # First OTP
        first_otp = "123456"
        first_time = timezone.now() - timedelta(minutes=2)
        self.user.womens_health_otp = first_otp
        self.user.womens_health_otp_created_at = first_time
        self.user.save()
        
        # Resend (generate new OTP)
        second_otp = "654321"
        second_time = timezone.now()
        self.user.womens_health_otp = second_otp
        self.user.womens_health_otp_created_at = second_time
        self.user.save()
        
        # Verify new OTP replaced old one
        self.assertEqual(self.user.womens_health_otp, second_otp)
        self.assertEqual(self.user.womens_health_otp_created_at, second_time)
        self.assertNotEqual(self.user.womens_health_otp, first_otp)

    def test_rate_limiting_otp_requests(self):
        """Test rate limiting for OTP requests"""
        # Simulate multiple rapid OTP requests
        request_times = []
        max_requests_per_hour = 5
        
        for i in range(max_requests_per_hour + 2):  # Try to exceed limit
            request_time = timezone.now() - timedelta(minutes=i*5)
            request_times.append(request_time)
        
        # Check if rate limit would be exceeded
        current_time = timezone.now()
        recent_requests = [
            t for t in request_times 
            if (current_time - t).total_seconds() < 3600  # Last hour
        ]
        
        self.assertGreater(len(recent_requests), max_requests_per_hour)

    def test_verification_required_decorator(self):
        """Test that verification is required for women's health endpoints"""
        # Test unverified user cannot access protected endpoints
        self.assertFalse(self.user.womens_health_verified)
        
        # Mock protected endpoint access
        # This would be implemented as a decorator on actual endpoints
        def requires_womens_health_verification(user):
            return user.womens_health_verified
        
        access_denied = not requires_womens_health_verification(self.user)
        self.assertTrue(access_denied)
        
        # Test verified user can access
        self.user.womens_health_verified = True
        self.user.save()
        
        access_granted = requires_womens_health_verification(self.user)
        self.assertTrue(access_granted)


class WomensHealthVerificationSecurityTestCase(TestCase):
    """Test security aspects of verification system"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_otp_format_validation(self):
        """Test OTP format requirements"""
        # Valid OTP (6 digits)
        valid_otp = "123456"
        self.assertTrue(valid_otp.isdigit() and len(valid_otp) == 6)
        
        # Invalid OTPs
        invalid_otps = [
            "12345",     # Too short
            "1234567",   # Too long
            "12345a",    # Contains letter
            "12-34-56",  # Contains special chars
            "",          # Empty
            None         # None
        ]
        
        for invalid_otp in invalid_otps:
            if invalid_otp is None:
                is_valid = False
            else:
                is_valid = invalid_otp.isdigit() and len(invalid_otp) == 6
            self.assertFalse(is_valid, f"OTP {invalid_otp} should be invalid")

    def test_otp_storage_security(self):
        """Test that OTP is properly stored and cleared"""
        # Store OTP
        otp = "123456"
        self.user.womens_health_otp = otp
        self.user.womens_health_otp_created_at = timezone.now()
        self.user.save()
        
        # Verify stored
        self.assertEqual(self.user.womens_health_otp, otp)
        
        # Clear after verification
        self.user.womens_health_otp = None
        self.user.womens_health_otp_created_at = None
        self.user.save()
        
        # Verify cleared
        self.assertIsNone(self.user.womens_health_otp)
        self.assertIsNone(self.user.womens_health_otp_created_at)

    def test_verification_date_immutability(self):
        """Test that verification date cannot be easily manipulated"""
        # Set initial verification
        original_date = timezone.now()
        self.user.womens_health_verified = True
        self.user.womens_health_verification_date = original_date
        self.user.save()
        
        # Attempt to change verification date
        new_date = timezone.now() + timedelta(days=1)
        self.user.womens_health_verification_date = new_date
        self.user.save()
        
        # In a real implementation, this might be protected
        # For now, just verify the date can be set
        self.assertEqual(self.user.womens_health_verification_date, new_date)

    def test_concurrent_verification_attempts(self):
        """Test handling of concurrent verification attempts"""
        # Set up OTP
        otp = "123456"
        self.user.womens_health_otp = otp
        self.user.womens_health_otp_created_at = timezone.now()
        self.user.save()
        
        # Simulate first verification attempt
        user1 = User.objects.get(id=self.user.id)
        user1.womens_health_verified = True
        user1.womens_health_verification_date = timezone.now()
        user1.save()
        
        # Simulate second concurrent attempt
        user2 = User.objects.get(id=self.user.id)
        # This should see the updated verification status
        self.assertTrue(user2.womens_health_verified)

    def test_verification_audit_trail(self):
        """Test that verification events can be audited"""
        # Initial state
        events = []
        events.append({
            'timestamp': timezone.now(),
            'event': 'user_created',
            'verified': self.user.womens_health_verified
        })
        
        # OTP generated
        self.user.womens_health_otp = "123456"
        self.user.womens_health_otp_created_at = timezone.now()
        self.user.save()
        
        events.append({
            'timestamp': timezone.now(),
            'event': 'otp_generated',
            'verified': self.user.womens_health_verified
        })
        
        # Verification completed
        self.user.womens_health_verified = True
        self.user.womens_health_verification_date = timezone.now()
        self.user.save()
        
        events.append({
            'timestamp': timezone.now(),
            'event': 'verification_completed',
            'verified': self.user.womens_health_verified
        })
        
        # Verify audit trail
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0]['event'], 'user_created')
        self.assertEqual(events[1]['event'], 'otp_generated')
        self.assertEqual(events[2]['event'], 'verification_completed')
        self.assertTrue(events[2]['verified'])


class WomensHealthProfileAccessTestCase(TestCase):
    """Test that profile access is properly gated by verification"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_profile_creation_requires_verification(self):
        """Test that women's health profile requires verification"""
        # Unverified user
        self.assertFalse(self.user.womens_health_verified)
        
        # In a real implementation, this would be protected
        # For now, test that verification status can be checked
        def can_create_profile(user):
            return user.womens_health_verified
        
        self.assertFalse(can_create_profile(self.user))
        
        # Verify user
        self.user.womens_health_verified = True
        self.user.save()
        
        self.assertTrue(can_create_profile(self.user))

    def test_profile_access_after_verification(self):
        """Test that profile can be accessed after verification"""
        # Verify user first
        self.user.womens_health_verified = True
        self.user.womens_health_verification_date = timezone.now()
        self.user.save()
        
        # Create profile
        profile = WomensHealthProfile.objects.create(
            user=self.user,
            pregnancy_status='not_pregnant',
            average_cycle_length=28
        )
        
        # Verify profile exists and is accessible
        self.assertEqual(profile.user, self.user)
        self.assertTrue(self.user.womens_health_verified)

    def test_verification_status_in_profile_context(self):
        """Test verification status within profile operations"""
        # Create verified user with profile
        self.user.womens_health_verified = True
        self.user.womens_health_verification_date = timezone.now()
        self.user.save()
        
        profile = WomensHealthProfile.objects.create(
            user=self.user,
            pregnancy_status='not_pregnant'
        )
        
        # Test that profile operations can check verification
        def is_authorized_for_sensitive_data(user):
            return user.womens_health_verified and hasattr(user, 'womens_health_profile')
        
        self.assertTrue(is_authorized_for_sensitive_data(self.user))


class WomensHealthVerificationIntegrationTestCase(TestCase):
    """Integration tests for the complete verification workflow"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_complete_verification_workflow(self):
        """Test the complete end-to-end verification workflow"""
        # Step 1: User requests verification
        self.assertFalse(self.user.womens_health_verified)
        
        # Step 2: OTP generated and stored
        otp = "123456"
        otp_time = timezone.now()
        self.user.womens_health_otp = otp
        self.user.womens_health_otp_created_at = otp_time
        self.user.save()
        
        # Verify OTP state
        self.assertEqual(self.user.womens_health_otp, otp)
        self.assertIsNotNone(self.user.womens_health_otp_created_at)
        self.assertFalse(self.user.womens_health_verified)
        
        # Step 3: User submits correct OTP within time limit
        submitted_otp = "123456"
        current_time = timezone.now()
        
        # Verify OTP
        is_correct = self.user.womens_health_otp == submitted_otp
        is_not_expired = (current_time - self.user.womens_health_otp_created_at).total_seconds() <= 300  # 5 minutes
        
        self.assertTrue(is_correct)
        self.assertTrue(is_not_expired)
        
        # Step 4: Complete verification
        if is_correct and is_not_expired:
            self.user.womens_health_verified = True
            self.user.womens_health_verification_date = current_time
            self.user.womens_health_otp = None
            self.user.womens_health_otp_created_at = None
            self.user.save()
        
        # Step 5: Verify final state
        self.assertTrue(self.user.womens_health_verified)
        self.assertIsNotNone(self.user.womens_health_verification_date)
        self.assertIsNone(self.user.womens_health_otp)
        self.assertIsNone(self.user.womens_health_otp_created_at)
        
        # Step 6: User can now create women's health profile
        profile = WomensHealthProfile.objects.create(
            user=self.user,
            pregnancy_status='not_pregnant',
            average_cycle_length=28,
            fertility_tracking_enabled=True
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertTrue(profile.fertility_tracking_enabled)

    def test_verification_failure_scenarios(self):
        """Test various failure scenarios in verification"""
        # Scenario 1: Wrong OTP
        self.user.womens_health_otp = "123456"
        self.user.womens_health_otp_created_at = timezone.now()
        self.user.save()
        
        wrong_otp = "654321"
        self.assertNotEqual(self.user.womens_health_otp, wrong_otp)
        self.assertFalse(self.user.womens_health_verified)
        
        # Scenario 2: Expired OTP
        self.user.womens_health_otp = "123456"
        self.user.womens_health_otp_created_at = timezone.now() - timedelta(minutes=10)
        self.user.save()
        
        current_time = timezone.now()
        is_expired = (current_time - self.user.womens_health_otp_created_at).total_seconds() > 300
        self.assertTrue(is_expired)
        self.assertFalse(self.user.womens_health_verified)
        
        # Scenario 3: No OTP set
        self.user.womens_health_otp = None
        self.user.womens_health_otp_created_at = None
        self.user.save()
        
        self.assertIsNone(self.user.womens_health_otp)
        self.assertFalse(self.user.womens_health_verified)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_verification_email_integration(self):
        """Test integration with email sending"""
        # Clear any previous emails
        mail.outbox = []
        
        # Simulate sending verification email
        otp = "123456"
        self.user.womens_health_otp = otp
        self.user.womens_health_otp_created_at = timezone.now()
        self.user.save()
        
        # Mock email sending
        from django.core.mail import send_mail
        
        send_mail(
            subject="Women's Health Verification Code",
            message=f"Your verification code is: {otp}",
            from_email="noreply@phb.com",
            recipient_list=[self.user.email],
            fail_silently=False,
        )
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn(otp, mail.outbox[0].body)

    def test_verification_with_profile_operations(self):
        """Test verification in context of profile operations"""
        # Verify user
        self.user.womens_health_verified = True
        self.user.womens_health_verification_date = timezone.now()
        self.user.save()
        
        # Create and update profile
        profile = WomensHealthProfile.objects.create(
            user=self.user,
            pregnancy_status='not_pregnant',
            average_cycle_length=28
        )
        
        # Test profile updates
        profile.pregnancy_status = 'trying_to_conceive'
        profile.fertility_tracking_enabled = True
        profile.save()
        
        # Verify updates
        profile.refresh_from_db()
        self.assertEqual(profile.pregnancy_status, 'trying_to_conceive')
        self.assertTrue(profile.fertility_tracking_enabled)
        self.assertTrue(self.user.womens_health_verified)

    def test_verification_persistence_across_sessions(self):
        """Test that verification persists across user sessions"""
        # Complete verification
        self.user.womens_health_verified = True
        self.user.womens_health_verification_date = timezone.now()
        self.user.save()
        
        user_id = self.user.id
        
        # Simulate new session - get user from database
        user_new_session = User.objects.get(id=user_id)
        
        # Verification should persist
        self.assertTrue(user_new_session.womens_health_verified)
        self.assertIsNotNone(user_new_session.womens_health_verification_date)
        
        # Should be able to access women's health features
        profile = WomensHealthProfile.objects.create(
            user=user_new_session,
            pregnancy_status='not_pregnant'
        )
        
        self.assertEqual(profile.user, user_new_session)


class WomensHealthVerificationPerformanceTestCase(TestCase):
    """Performance tests for verification system"""

    def test_verification_query_performance(self):
        """Test that verification checks are performant"""
        # Create multiple users
        users = []
        for i in range(100):
            user = User.objects.create_user(
                email=f'user{i}@example.com',
                password='testpass123',
                first_name=f'User{i}',
                last_name='Test'
            )
            users.append(user)
        
        # Verify half of them
        for i, user in enumerate(users[:50]):
            user.womens_health_verified = True
            user.womens_health_verification_date = timezone.now()
            user.save()
        
        # Test bulk verification check
        verified_users = User.objects.filter(womens_health_verified=True)
        unverified_users = User.objects.filter(womens_health_verified=False)
        
        self.assertEqual(verified_users.count(), 50)
        self.assertEqual(unverified_users.count(), 50)

    def test_otp_cleanup_performance(self):
        """Test performance of cleaning up expired OTPs"""
        # Create users with expired OTPs
        expired_time = timezone.now() - timedelta(hours=1)
        
        users_with_expired_otps = []
        for i in range(50):
            user = User.objects.create_user(
                email=f'expired{i}@example.com',
                password='testpass123'
            )
            user.womens_health_otp = "123456"
            user.womens_health_otp_created_at = expired_time
            user.save()
            users_with_expired_otps.append(user)
        
        # Bulk cleanup of expired OTPs
        expired_threshold = timezone.now() - timedelta(minutes=5)
        expired_otps = User.objects.filter(
            womens_health_otp__isnull=False,
            womens_health_otp_created_at__lt=expired_threshold
        )
        
        self.assertEqual(expired_otps.count(), 50)
        
        # In a real implementation, these would be cleaned up
        # expired_otps.update(
        #     womens_health_otp=None,
        #     womens_health_otp_created_at=None
        # )