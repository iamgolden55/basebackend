from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from api.models import CustomUser
from django.core import mail

class ChangePasswordTests(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = CustomUser.objects.create_user(
            email='testuser@example.com',
            password='oldpassword123',
            first_name='Test',
            last_name='User'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        # Get JWT token for authentication
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'testuser@example.com',
            'password': 'oldpassword123',
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # URL for change password
        self.url = reverse('password-change')
        
    def test_change_password_success(self):
        """Test successful password change with correct current password"""
        # Clear the test outbox
        mail.outbox = []
        
        data = {
            'current_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data.get('message', '').lower())
        
        # Verify the password was actually changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
        
        # Check that a confirmation email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['testuser@example.com'])
        self.assertIn('Password Changed', mail.outbox[0].subject)
        
    def test_change_password_wrong_current(self):
        """Test password change with incorrect current password"""
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('incorrect', response.data.get('error', '').lower())
        
        # Verify the password was not changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('oldpassword123'))
    
    def test_change_password_mismatch(self):
        """Test password change with mismatched new passwords"""
        data = {
            'current_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("don't match", response.data.get('confirm_password', [''])[0].lower())
        
        # Verify the password was not changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('oldpassword123'))
    
    def test_change_password_unauthenticated(self):
        """Test password change without authentication"""
        # Remove authentication credentials
        self.client.credentials()
        
        data = {
            'current_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Verify the password was not changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('oldpassword123')) 