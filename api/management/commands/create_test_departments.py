from django.core.management.base import BaseCommand
from api.models.medical.department import Department
from api.models.medical.hospital_auth import Hospital

class Command(BaseCommand):
    help = 'Creates test departments for a hospital'

    def handle(self, *args, **options):
        # Create a default hospital if none exists
        hospital, created = Hospital.objects.get_or_create(
            name="General Hospital",
            defaults={
                'address': '123 Medical Drive',
                'city': 'Healthcare City',
                'state': 'Medical State',
                'zip_code': '12345',
                'country': 'United States',
                'phone': '555-123-4567',
                'email': 'info@generalhospital.com',
                'website': 'https://generalhospital.com'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created hospital: {hospital.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing hospital: {hospital.name}'))
        
        # Create default departments
        departments = [
            {
                'name': 'Cardiology',
                'code': 'CARD01',
                'description': 'Heart and cardiovascular system',
                'department_type': 'medical',
                'floor_number': '3',
                'wing': 'north',
                'extension_number': '1234',
                'emergency_contact': '911',
                'email': 'cardio@hospital.com',
                'minimum_staff_required': 2,
                'current_staff_count': 5,
                'total_beds': 20,
                'occupied_beds': 0,
                'icu_beds': 5,
                'occupied_icu_beds': 0,
                'bed_capacity': 25,
                'hospital': hospital
            },
            {
                'name': 'Dermatology',
                'code': 'DERM01',
                'description': 'Skin, hair, and nails',
                'department_type': 'medical',
                'floor_number': '2',
                'wing': 'east',
                'extension_number': '2345',
                'emergency_contact': '912',
                'email': 'derm@hospital.com',
                'minimum_staff_required': 2,
                'current_staff_count': 4,
                'total_beds': 10,
                'occupied_beds': 0,
                'icu_beds': 0,
                'occupied_icu_beds': 0,
                'bed_capacity': 10,
                'hospital': hospital
            },
            {
                'name': 'Neurology',
                'code': 'NEUR01',
                'description': 'Brain, spinal cord, and nervous system',
                'department_type': 'medical',
                'floor_number': '4',
                'wing': 'west',
                'extension_number': '3456',
                'emergency_contact': '913',
                'email': 'neuro@hospital.com',
                'minimum_staff_required': 3,
                'current_staff_count': 6,
                'total_beds': 15,
                'occupied_beds': 0,
                'icu_beds': 5,
                'occupied_icu_beds': 0,
                'bed_capacity': 20,
                'hospital': hospital
            },
            {
                'name': 'Orthopedics',
                'code': 'ORTH01',
                'description': 'Bones, joints, ligaments, tendons, and muscles',
                'department_type': 'medical',
                'floor_number': '3',
                'wing': 'south',
                'extension_number': '4567',
                'emergency_contact': '914',
                'email': 'ortho@hospital.com',
                'minimum_staff_required': 2,
                'current_staff_count': 5,
                'total_beds': 20,
                'occupied_beds': 0,
                'icu_beds': 0,
                'occupied_icu_beds': 0,
                'bed_capacity': 20,
                'hospital': hospital
            },
            {
                'name': 'Pediatrics',
                'code': 'PEDI01',
                'description': 'Medical care for infants, children, and adolescents',
                'department_type': 'medical',
                'floor_number': '1',
                'wing': 'west',
                'extension_number': '5678',
                'emergency_contact': '915',
                'email': 'peds@hospital.com',
                'minimum_staff_required': 3,
                'current_staff_count': 7,
                'total_beds': 25,
                'occupied_beds': 0,
                'icu_beds': 5,
                'occupied_icu_beds': 0,
                'bed_capacity': 30,
                'hospital': hospital
            },
            {
                'name': 'Psychiatry',
                'code': 'PSYC01',
                'description': 'Mental, emotional, and behavioral disorders',
                'department_type': 'medical',
                'floor_number': '5',
                'wing': 'east',
                'extension_number': '6789',
                'emergency_contact': '916',
                'email': 'psych@hospital.com',
                'minimum_staff_required': 2,
                'current_staff_count': 4,
                'total_beds': 15,
                'occupied_beds': 0,
                'icu_beds': 0,
                'occupied_icu_beds': 0,
                'bed_capacity': 15,
                'hospital': hospital
            },
            {
                'name': 'Oncology',
                'code': 'ONCO01',
                'description': 'Cancer diagnosis and treatment',
                'department_type': 'medical',
                'floor_number': '4',
                'wing': 'north',
                'extension_number': '7890',
                'emergency_contact': '917',
                'email': 'onco@hospital.com',
                'minimum_staff_required': 3,
                'current_staff_count': 6,
                'total_beds': 20,
                'occupied_beds': 0,
                'icu_beds': 5,
                'occupied_icu_beds': 0,
                'bed_capacity': 25,
                'hospital': hospital
            },
            {
                'name': 'Gynecology',
                'code': 'GYNE01',
                'description': 'Female reproductive system',
                'department_type': 'medical',
                'floor_number': '2',
                'wing': 'west',
                'extension_number': '8901',
                'emergency_contact': '918',
                'email': 'gyn@hospital.com',
                'minimum_staff_required': 2,
                'current_staff_count': 5,
                'total_beds': 15,
                'occupied_beds': 0,
                'icu_beds': 0,
                'occupied_icu_beds': 0,
                'bed_capacity': 15,
                'hospital': hospital
            }
        ]
        
        # First delete any existing departments to start fresh
        Department.objects.all().delete()
        self.stdout.write(self.style.WARNING('Deleted existing departments'))
        
        departments_created = 0
        for dept_data in departments:
            try:
                department = Department.objects.create(**dept_data)
                departments_created += 1
                self.stdout.write(self.style.SUCCESS(f'Created department: {department.name}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating {dept_data["name"]}: {str(e)}'))
                
        self.stdout.write(self.style.SUCCESS(f'Created {departments_created} test departments')) 