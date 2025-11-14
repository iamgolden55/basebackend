"""
Django management command to create a test prescription with auto-pharmacy assignment.

Usage:
    python manage.py create_test_prescription --email user@example.com
    python manage.py create_test_prescription --hpn HPN12345678
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from api.models import MedicalRecord, Medication, NominatedPharmacy
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create a test prescription for a patient (auto-assigns nominated pharmacy)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Patient email address',
        )
        parser.add_argument(
            '--hpn',
            type=str,
            help='Patient HPN (Health Patient Number)',
        )
        parser.add_argument(
            '--medication',
            type=str,
            default='Amoxicillin',
            help='Medication name (default: Amoxicillin)',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        hpn = options.get('hpn')
        medication_name = options.get('medication')

        # Get patient
        try:
            if email:
                patient = User.objects.get(email=email)
                self.stdout.write(f"Found patient by email: {patient.email}")
            elif hpn:
                patient = User.objects.get(hpn=hpn)
                self.stdout.write(f"Found patient by HPN: {patient.hpn}")
            else:
                raise CommandError(
                    'Please provide either --email or --hpn to identify the patient'
                )
        except User.DoesNotExist:
            raise CommandError(
                f'Patient not found with {"email: " + email if email else "HPN: " + hpn}'
            )

        # Check for nominated pharmacy
        nomination = NominatedPharmacy.objects.filter(
            user=patient,
            is_current=True
        ).first()

        if nomination:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Patient has nominated pharmacy: {nomination.pharmacy.name}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '⚠ Patient has NO nominated pharmacy - prescription will be created without pharmacy'
                )
            )

        # Get or create medical record
        medical_record, created = MedicalRecord.objects.get_or_create(
            user=patient,
            defaults={
                'blood_type': 'O+',
                'allergies': 'None',
                'chronic_conditions': 'None'
            }
        )

        if created:
            self.stdout.write(f"Created new medical record for patient")
        else:
            self.stdout.write(f"Using existing medical record (ID: {medical_record.id})")

        # Create prescription (Medication.save() will auto-assign pharmacy)
        try:
            from django.utils import timezone

            medication = Medication.objects.create(
                medical_record=medical_record,
                medication_name=medication_name,
                strength='500mg',
                form='Tablet',
                route='Oral',
                dosage='1 tablet',
                frequency='Three times daily',
                duration='7 days',
                start_date=timezone.now().date(),
                patient_instructions='Take with food. Complete the full course.',
                indication='Test prescription',
                status='active'
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Successfully created prescription!'
                )
            )
            self.stdout.write(f'  Medication ID: {medication.id}')
            self.stdout.write(f'  Medication: {medication.medication_name} {medication.strength}')
            self.stdout.write(f'  Dosage: {medication.dosage} {medication.frequency}')
            self.stdout.write(f'  Duration: {medication.duration}')

            if medication.nominated_pharmacy:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ AUTO-ASSIGNED Pharmacy: {medication.nominated_pharmacy.name}'
                    )
                )
                self.stdout.write(f'    Pharmacy Code: {medication.nominated_pharmacy.phb_pharmacy_code}')
                self.stdout.write(f'    Address: {medication.nominated_pharmacy.address_line_1}, {medication.nominated_pharmacy.city}')
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '  ⚠ No pharmacy assigned (patient has no nominated pharmacy)'
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Test prescription created successfully!'
                )
            )

        except Exception as e:
            logger.error(f"Error creating test prescription: {str(e)}")
            raise CommandError(f'Failed to create prescription: {str(e)}')
