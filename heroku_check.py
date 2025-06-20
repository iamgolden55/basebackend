print("Checking users on Heroku database...")

from api.models import CustomUser

# Count users
user_count = CustomUser.objects.count()
print(f'Heroku database has {user_count} total users')

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
