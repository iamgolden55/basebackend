# Non-interactive script to test email functionality
import os
from dotenv import load_dotenv
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

load_dotenv()  # Load environment variables

# Your email address where you want to receive the test
# Replace this with your actual email or pass as command line argument
DEFAULT_TEST_EMAIL = 'test@example.com'  # Will be overridden if provided as argument

def test_email():
    recipient_email = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TEST_EMAIL
    
    print("Email settings:")
    print(f"EMAIL_HOST: {os.environ.get('EMAIL_HOST')}")
    print(f"EMAIL_PORT: {os.environ.get('EMAIL_PORT')}")
    print(f"EMAIL_HOST_USER: {os.environ.get('EMAIL_HOST_USER')}")
    print(f"DEFAULT_FROM_EMAIL: {os.environ.get('DEFAULT_FROM_EMAIL')}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_PASSWORD is {'set' if os.environ.get('EMAIL_HOST_PASSWORD') else 'NOT SET'}")
    print(f"Sending test email to: {recipient_email}")
    
    # Simple context for template
    context = {
        'reset_link': 'http://test-link.com',
        'user_name': 'Test User',
        'country': 'Test Country',
        'city': 'Test City',
        'ip_address': '127.0.0.1',
        'device': 'Test Device',
        'date': 'May 23, 2025'
    }
    
    print("\nSending test email...")
    try:
        send_mail(
            'Test Email from PHB Backend',
            'This is a test email to check SMTP configuration.',
            os.environ.get('DEFAULT_FROM_EMAIL'),
            [recipient_email],
            fail_silently=False
        )
        print("Email sent successfully!")
    except Exception as e:
        print(f"\nError sending email: {e}")
        
        # Additional debugging info based on the error
        print("\nPossible solutions:")
        print("1. Check if EMAIL_HOST_PASSWORD is correctly set in your .env file")
        print("2. If using Gmail:")
        print("   - You need an App Password (not your regular Gmail password)")
        print("   - Generate one at: https://myaccount.google.com/apppasswords")
        print("3. Check if your antivirus or firewall is blocking SMTP connections")
        print("4. Make sure your FROM email address matches your SMTP credentials")

if __name__ == "__main__":
    test_email()
