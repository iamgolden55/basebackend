import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# Import the models
from api.models import CustomUser

def check_users():
    # Count users
    user_count = CustomUser.objects.count()
    print(f'Database has {user_count} total users')
    
    # Print sample users
    print('\nSample users:')
    for user in CustomUser.objects.all()[:5]:
        print(f'- {user.email} (ID: {user.id})')
    
    # Count users by role
    print('\nUsers by role:')
    roles = ['patient', 'doctor', 'nurse', 'admin', 'hospital_admin']
    for role in roles:
        count = CustomUser.objects.filter(role=role).count()
        print(f'- {role}: {count}')

if __name__ == '__main__':
    check_users()
