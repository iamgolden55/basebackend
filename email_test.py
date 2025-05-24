# Script to test email functionality
import os
from dotenv import load_dotenv
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

load_dotenv()  # Load environment variables

def test_email():
    print("Email settings:")
    print(f"EMAIL_HOST: {os.environ.get('EMAIL_HOST')}")
    print(f"EMAIL_PORT: {os.environ.get('EMAIL_PORT')}")
    print(f"EMAIL_HOST_USER: {os.environ.get('EMAIL_HOST_USER')}")
    print(f"DEFAULT_FROM_EMAIL: {os.environ.get('DEFAULT_FROM_EMAIL')}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    
    recipient_email = input("Enter your email address to receive the test: ")
    
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
            html_message=render_to_string('email/reset-password.html', context)
        )
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
        
        # Additional debugging info
        print("\nMake sure you have:")
        print("1. Correct EMAIL_HOST_PASSWORD in your .env file")
        print("2. 'Less secure apps' enabled or an App Password if using Gmail")
        print("3. No network restrictions blocking SMTP traffic")

if __name__ == "__main__":
    test_email()
