from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from api.models import CustomUser, Hospital
from api.models.medical.hospital_auth import HospitalAdmin

class Command(BaseCommand):
    help = "Update a hospital admin's email address for testing"

    def add_arguments(self, parser):
        parser.add_argument('--hospital_code', type=str, required=True, help='Hospital registration code')
        parser.add_argument('--email', type=str, required=True, help='New email address for the admin')

    def handle(self, *args, **options):
        hospital_code = options['hospital_code']
        new_email = options['email']
        
        with transaction.atomic():
            try:
                # Find the hospital
                try:
                    hospital = Hospital.objects.get(registration_number=hospital_code)
                except Hospital.DoesNotExist:
                    try:
                        # Try by ID if code is numeric
                        if hospital_code.isdigit():
                            hospital = Hospital.objects.get(id=int(hospital_code))
                        else:
                            raise Hospital.DoesNotExist
                    except Hospital.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'Hospital with code {hospital_code} not found'))
                        return
                
                # Find the admin for this hospital
                try:
                    admin = HospitalAdmin.objects.filter(hospital=hospital).first()
                    if not admin:
                        self.stdout.write(self.style.ERROR(f'No admin found for hospital {hospital.name}'))
                        return
                        
                    # Update the email
                    user = admin.user
                    old_email = user.email
                    user.email = new_email
                    user.username = new_email  # Also update username if it's the same as email
                    user.save()
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'Successfully updated admin email for {hospital.name} from {old_email} to {new_email}'
                    ))
                    self.stdout.write(self.style.SUCCESS(
                        f'You can now login with:\nEmail: {new_email}\nPassword: Password123!\nHospital Code: {hospital_code}'
                    ))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error updating admin: {str(e)}'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
