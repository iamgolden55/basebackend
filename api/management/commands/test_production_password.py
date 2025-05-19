# api/management/commands/test_production_password.py

import logging
import string
import random
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


def generate_secure_password():
    """
    Generate a secure password following best practices for hospital admins.
    The password has a minimum length of 12 characters and includes uppercase, lowercase,
    digits, and special characters.
    """
    length = 14  # Increased from 12 to 14 for production
    
    # Ensure we have at least one of each character type
    uppercase = random.choice(string.ascii_uppercase)
    lowercase = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    special = random.choice('!@#$%^&*()-_=+[]{}|;:,.<>?')
    
    # Fill the rest with a mix of all characters
    remaining_length = length - 4
    all_chars = string.ascii_letters + string.digits + '!@#$%^&*()-_=+[]{}|;:,.<>?'
    remaining_chars = ''.join(random.choice(all_chars) for _ in range(remaining_length))
    
    # Combine all parts and shuffle
    password_chars = list(uppercase + lowercase + digit + special + remaining_chars)
    random.shuffle(password_chars)
    return ''.join(password_chars)


class Command(BaseCommand):
    help = 'Generates and displays sample production-mode secure passwords'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5, help='Number of sample passwords to generate')

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(self.style.SUCCESS(f"Generating {count} sample production-mode passwords:"))
        
        for i in range(count):
            password = generate_secure_password()
            self.stdout.write(f"Password {i+1}: {password}")
            
            # Analyze password strength
            entropy = len(password) * (len(string.ascii_letters + string.digits + string.punctuation))
            strength = "Strong" if entropy > 80 else "Medium"
            
            # Check for requirements
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(not c.isalnum() for c in password)
            requirements_met = all([has_upper, has_lower, has_digit, has_special])
            
            self.stdout.write(f"   - Length: {len(password)}")
            self.stdout.write(f"   - Contains uppercase: {has_upper}")
            self.stdout.write(f"   - Contains lowercase: {has_lower}")
            self.stdout.write(f"   - Contains digit: {has_digit}")
            self.stdout.write(f"   - Contains special: {has_special}")
            self.stdout.write(f"   - All requirements met: {requirements_met}")
            self.stdout.write(f"   - Strength rating: {strength}")
            
        self.stdout.write(self.style.SUCCESS("\nIn production mode, your system will generate passwords like these for hospital admins."))
        self.stdout.write(self.style.SUCCESS("They will be required to change this password on first login for added security."))
