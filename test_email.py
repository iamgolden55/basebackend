import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

def test_suspicious_login_email():
    """Test sending a suspicious login email to eruwagolden@gmail.com"""
    
    # Email configuration
    from_email = os.environ.get('DEFAULT_FROM_EMAIL')
    to_email = 'eruwagolden@gmail.com'  # Test recipient
    
    # Print email configuration
    print(f"Email configuration:")
    print(f"  From: {from_email}")
    print(f"  To: {to_email}")
    print(f"  EMAIL_HOST: {os.environ.get('EMAIL_HOST')}")
    print(f"  EMAIL_PORT: {os.environ.get('EMAIL_PORT')}")
    print(f"  EMAIL_HOST_USER: {os.environ.get('EMAIL_HOST_USER')}")
    
    # Prepare context for email template
    context = {
        'user': {'first_name': 'Test', 'email': 'eruwagolden55@gmail.com'},
        'ip_address': '192.168.1.1',
        'location': 'Unknown Location',
        'device': 'Test Device',
        'timestamp': timezone.now().strftime('%b %d %Y %H:%M:%S %Z'),
        'frontend_url': os.environ.get('NEXTJS_URL', 'http://localhost:3000')
    }
    
    try:
        # Render the email template
        html_message = render_to_string('email/suspicious_login.html', context)
        plain_message = strip_tags(html_message)
        print("Email template rendered successfully")
        
        # Send the email
        print(f"Attempting to send test email to {to_email}...")
        result = send_mail(
            subject='PHB Healthcare - Test Suspicious Login Alert',
            message=plain_message,
            from_email=from_email,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"Email sent successfully! Result: {result}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting email test...")
    test_suspicious_login_email()
    print("Email test completed.")
