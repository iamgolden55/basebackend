from django.core.management.base import BaseCommand
from api.models import Hospital
from api.models.medical.department import Department

class Command(BaseCommand):
    help = 'Add common medical departments to St. Nicholas Hospital Lagos.'

    def handle(self, *args, **options):
        try:
            hospital = Hospital.objects.get(name='St. Nicholas Hospital Lagos')
        except Hospital.DoesNotExist:
            self.stdout.write(self.style.ERROR('Hospital not found.'))
            return

        new_depts = [
            ('Cardiology', 'CARD201', 'medical'),
            ('Orthopedics', 'ORTH202', 'medical'),
            ('Neurology', 'NEUR203', 'medical'),
            ('General Medicine', 'GENM204', 'medical'),
            ('Dermatology', 'DERM205', 'medical'),
            ('ENT', 'ENT206', 'medical'),
            ('Gastroenterology', 'GAST207', 'medical'),
            ('Urology', 'UROL208', 'medical'),
            ('Psychiatry', 'PSYC209', 'medical'),
            ('Pediatrics', 'PEDI210', 'medical'),
            ('Gynecology', 'GYNE211', 'medical'),
            ('Ophthalmology', 'OPHT212', 'medical'),
        ]
        count = 0
        for name, code, dept_type in new_depts:
            dept, created = Department.objects.get_or_create(
                hospital=hospital,
                name=name,
                code=code,
                department_type=dept_type,
                defaults={
                    'current_staff_count': 1,
                    'minimum_staff_required': 1,
                    'floor_number': '1',
                    'wing': 'north',
                    'extension_number': '1001',
                    'emergency_contact': '+2348000000000',
                    'email': f'{code.lower()}@stnicholas.com',
                    'is_24_hours': True,
                    'operating_hours': {
                        day: {'start': '00:00', 'end': '23:59'} for day in [
                            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
                        ]
                    },
                }
            )
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Added department: {name}'))
            else:
                self.stdout.write(f'Department already exists: {name}')
        self.stdout.write(self.style.SUCCESS(f'Total departments added: {count}')) 