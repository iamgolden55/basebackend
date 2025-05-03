from django.core.management.base import BaseCommand
from api.models.medical.hospital import Hospital
from api.models.medical.department import Department
from api.models.medical.appointment import AppointmentType
from django.db import transaction
import random

NIGERIAN_STATES = [
    'Lagos', 'Kano', 'Rivers', 'Kaduna', 'Oyo', 'Enugu', 'Edo', 'Plateau', 'Borno', 'Akwa Ibom'
]

HOSPITAL_NAMES = [
    'St. Nicholas Hospital', 'Eko Medical Centre', 'First Consultants Hospital',
    'Lifeline Children Hospital', 'Reddington Hospital', 'Lagoon Hospital',
    'University College Hospital', 'Federal Medical Centre', 'General Hospital',
    'Nisa Premier Hospital'
]

EXTRA_HOSPITAL_NAMES = [
    'Delta Specialist Hospital', 'Warri Central Hospital', 'Asaba Medical Centre',
    'Port Harcourt Teaching Hospital', 'Rivers State Hospital', 'PHC General Hospital',
    'Abuja National Hospital', 'Garki Hospital', 'Wuse District Hospital',
    'Kaduna State University Hospital', 'Barau Dikko Hospital', 'Zaria Specialist Hospital',
    'Sapele General Hospital', 'Ughelli Medical Centre', 'Bonny Island Hospital',
    'Obio Cottage Hospital', 'Maitama District Hospital', 'Kubwa General Hospital',
    'Kafanchan General Hospital', 'Kagoro Medical Centre'
]

EXTRA_LOCATIONS = [
    ('Delta', 'Delta State'),
    ('Port Harcourt', 'Rivers State'),
    ('Abuja', 'FCT'),
    ('Kaduna', 'Kaduna State'),
]

DEPARTMENT_TEMPLATES = [
    {
        'name': 'Cardiology', 'department_type': 'medical', 'wing': 'north', 'floor_number': '3',
        'description': 'Heart and cardiovascular system',
    },
    {
        'name': 'Neurology', 'department_type': 'medical', 'wing': 'west', 'floor_number': '4',
        'description': 'Brain and nervous system',
    },
    {
        'name': 'Pediatrics', 'department_type': 'medical', 'wing': 'east', 'floor_number': '2',
        'description': 'Children health',
    },
    {
        'name': 'Emergency', 'department_type': 'emergency', 'wing': 'central', 'floor_number': '1',
        'description': 'Emergency care',
    },
    {
        'name': 'Radiology', 'department_type': 'radiology', 'wing': 'south', 'floor_number': '2',
        'description': 'Imaging and diagnostics',
    },
    {
        'name': 'Pharmacy', 'department_type': 'pharmacy', 'wing': 'east', 'floor_number': '1',
        'description': 'Medication and prescriptions',
    },
    {
        'name': 'Surgery', 'department_type': 'surgical', 'wing': 'west', 'floor_number': '5',
        'description': 'Surgical operations',
    },
    {
        'name': 'Outpatient', 'department_type': 'outpatient', 'wing': 'north', 'floor_number': '1',
        'description': 'Outpatient clinic',
    },
]

APPOINTMENT_TYPE_CHOICES = [
    ('first_visit', 'First Visit'),
    ('follow_up', 'Follow Up'),
    ('consultation', 'Consultation'),
    ('procedure', 'Procedure'),
    ('test', 'Medical Test'),
    ('vaccination', 'Vaccination'),
    ('therapy', 'Therapy'),
]

class Command(BaseCommand):
    help = 'Creates 10 Nigerian hospitals with 5-7 departments and appointment types per hospital.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Deleting existing hospitals, departments, and appointment types...'))
        Department.objects.all().delete()
        Hospital.objects.all().delete()
        AppointmentType.objects.all().delete()

        for i in range(10):
            hospital_name = HOSPITAL_NAMES[i % len(HOSPITAL_NAMES)] + f' {NIGERIAN_STATES[i]}'
            state = NIGERIAN_STATES[i]
            hospital = Hospital.objects.create(
                name=hospital_name,
                address=f'{random.randint(1, 100)} {state} Road',
                city=state + ' City',
                state=state,
                country='Nigeria',
                registration_number=f'NGH-{i+1:03d}',
                hospital_type=random.choice(['public', 'private', 'specialist', 'teaching']),
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created hospital: {hospital.name}'))

            num_departments = random.randint(5, 7)
            used_templates = random.sample(DEPARTMENT_TEMPLATES, num_departments)
            for j, dept_tpl in enumerate(used_templates):
                dept_code = f'{dept_tpl["name"][:4].upper()}{i+1}{j+1:02d}'
                department = Department.objects.create(
                    name=dept_tpl['name'],
                    code=dept_code,
                    department_type=dept_tpl['department_type'],
                    description=dept_tpl['description'],
                    floor_number=dept_tpl['floor_number'],
                    wing=dept_tpl['wing'],
                    extension_number=str(2000 + j),
                    emergency_contact=f'080{random.randint(10000000,99999999)}',
                    email=f'{dept_tpl["name"].lower()}@{hospital.name.lower().replace(" ","")}.com',
                    is_active=True,
                    is_24_hours=random.choice([True, False]),
                    operating_hours={day: {'start': '08:00', 'end': '17:00'} for day in ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']},
                    total_beds=random.randint(10, 30),
                    occupied_beds=0,
                    icu_beds=random.randint(0, 10),
                    occupied_icu_beds=0,
                    bed_capacity=0,  # will be set in save()
                    current_patient_count=0,
                    minimum_staff_required=random.randint(2, 5),
                    current_staff_count=random.randint(5, 10),
                    recommended_staff_ratio=1.0,
                    annual_budget=10000000.00,
                    budget_year=2024,
                    budget_utilized=0,
                    equipment_budget=2000000.00,
                    staff_budget=5000000.00,
                    appointment_duration=30,
                    max_daily_appointments=50,
                    requires_referral=random.choice([True, False]),
                    hospital=hospital
                )
                self.stdout.write(self.style.SUCCESS(f'  Created department: {department.name} ({department.code})'))

            # Create appointment types for this hospital
            for atype, atype_name in APPOINTMENT_TYPE_CHOICES:
                AppointmentType.objects.create(
                    id=f"{atype}_{hospital.id}",
                    name=atype_name,
                    description=f'{atype_name} at {hospital.name}',
                    is_active=True,
                    hospital=hospital
                )
            self.stdout.write(self.style.SUCCESS(f'  Created appointment types for {hospital.name}'))

        # Create default appointment types (not linked to any hospital)
        for atype, atype_name in APPOINTMENT_TYPE_CHOICES:
            AppointmentType.objects.get_or_create(
                id=atype,
                name=atype_name,
                defaults={
                    'description': f'Default {atype_name} (for hospitals without specific types)',
                    'is_active': True,
                    'hospital': None
                }
            )
        self.stdout.write(self.style.SUCCESS('Created default appointment types (global)'))

        # Add 20 extra hospitals, evenly distributed
        for i in range(20):
            name_idx = i % len(EXTRA_HOSPITAL_NAMES)
            loc_idx = i % 4
            city, state = EXTRA_LOCATIONS[loc_idx]
            hospital_name = f"{EXTRA_HOSPITAL_NAMES[name_idx]} {city}"
            reg_num = f'NGH-X{i+1:03d}'
            hospital = Hospital.objects.create(
                name=hospital_name,
                address=f'{random.randint(1, 100)} {city} Road',
                city=city,
                state=state,
                country='Nigeria',
                registration_number=reg_num,
                hospital_type=random.choice(['public', 'private', 'specialist', 'teaching']),
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created hospital: {hospital.name}'))

            num_departments = random.randint(5, 7)
            used_templates = random.sample(DEPARTMENT_TEMPLATES, num_departments)
            for j, dept_tpl in enumerate(used_templates):
                dept_code = f'{dept_tpl["name"][:4].upper()}X{i+1}{j+1:02d}'
                department = Department.objects.create(
                    name=dept_tpl['name'],
                    code=dept_code,
                    department_type=dept_tpl['department_type'],
                    description=dept_tpl['description'],
                    floor_number=dept_tpl['floor_number'],
                    wing=dept_tpl['wing'],
                    extension_number=str(3000 + j),
                    emergency_contact=f'080{random.randint(10000000,99999999)}',
                    email=f'{dept_tpl["name"].lower()}@{hospital.name.lower().replace(" ","")}.com',
                    is_active=True,
                    is_24_hours=random.choice([True, False]),
                    operating_hours={day: {'start': '08:00', 'end': '17:00'} for day in ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']},
                    total_beds=random.randint(10, 30),
                    occupied_beds=0,
                    icu_beds=random.randint(0, 10),
                    occupied_icu_beds=0,
                    bed_capacity=0,  # will be set in save()
                    current_patient_count=0,
                    minimum_staff_required=random.randint(2, 5),
                    current_staff_count=random.randint(5, 10),
                    recommended_staff_ratio=1.0,
                    annual_budget=10000000.00,
                    budget_year=2024,
                    budget_utilized=0,
                    equipment_budget=2000000.00,
                    staff_budget=5000000.00,
                    appointment_duration=30,
                    max_daily_appointments=50,
                    requires_referral=random.choice([True, False]),
                    hospital=hospital
                )
                self.stdout.write(self.style.SUCCESS(f'  Created department: {department.name} ({department.code})'))

            # Create appointment types for this hospital
            for atype, atype_name in APPOINTMENT_TYPE_CHOICES:
                AppointmentType.objects.create(
                    id=f"{atype}_{hospital.id}",
                    name=atype_name,
                    description=f'{atype_name} at {hospital.name}',
                    is_active=True,
                    hospital=hospital
                )
            self.stdout.write(self.style.SUCCESS(f'  Created appointment types for {hospital.name}'))

        self.stdout.write(self.style.SUCCESS('All Nigerian hospitals, departments, and appointment types created!')) 