from django.core.management.base import BaseCommand
from api.models.user.custom_user import CustomUser
from api.models.medical_staff.doctor import Doctor
from api.models.medical.department import Department
from api.models.medical.hospital import Hospital
from django.utils import timezone
import random
import datetime
import uuid

NIGERIAN_FIRST_NAMES = [
    'Chinedu', 'Aisha', 'Emeka', 'Ngozi', 'Bola', 'Ifeanyi', 'Fatima', 'Tunde', 'Uche', 'Yemi',
    'Sani', 'Ada', 'Segun', 'Blessing', 'Ibrahim', 'Kemi', 'Chika', 'Hauwa', 'Gbenga', 'Amaka'
]
NIGERIAN_LAST_NAMES = [
    'Okafor', 'Balogun', 'Abubakar', 'Eze', 'Ogunleye', 'Mohammed', 'Nwosu', 'Adebayo', 'Danladi', 'Okoro',
    'Ojo', 'Aliyu', 'Onyeka', 'Lawal', 'Obi', 'Yusuf', 'Oladipo', 'Ibrahim', 'Chukwu', 'Garba'
]
NIGERIAN_LANGUAGES = [
    ('en', 'English'),
    ('yo', 'Yoruba'),
    ('ig', 'Igbo'),
    ('ha', 'Hausa'),
    ('ib', 'Ibibio'),
    ('be', 'Bini'),
    ('ur', 'Urhobo'),
    ('ef', 'Efik'),
    ('tv', 'Tiv'),
    ('id', 'Idoma'),
]

QUALIFICATIONS = [
    ['MBBS', 'FWACS'],
    ['MBBS', 'FMCP'],
    ['MBBS', 'FWACP'],
    ['MBBS', 'FMCPath'],
    ['MBBS', 'FMCORL'],
    ['MBBS', 'FWACS', 'MSc'],
]

class Command(BaseCommand):
    help = 'Creates 3 random Nigerian doctors for every department in every hospital.'

    def handle(self, *args, **options):
        departments = Department.objects.select_related('hospital').all()
        created_count = 0
        for dept in departments:
            hospital = dept.hospital
            for i in range(3):
                first_name = random.choice(NIGERIAN_FIRST_NAMES)
                last_name = random.choice(NIGERIAN_LAST_NAMES)
                unique_part = uuid.uuid4().hex[:6]
                email = f"{first_name.lower()}.{last_name.lower()}.{dept.id}{i}.{unique_part}@{hospital.name.lower().replace(' ','')}.com"
                language_code, language_name = random.choice(NIGERIAN_LANGUAGES)
                city = hospital.city or ''
                state = hospital.state or ''
                # Ensure unique NIN for user
                nin = str(random.randint(10000000000, 99999999999))
                # Create user
                user = CustomUser.objects.create_user(
                    email=email,
                    password='doctorpass123',
                    first_name=first_name,
                    last_name=last_name,
                    role='doctor',
                    city=city,
                    state=state,
                    preferred_language=language_code,
                    secondary_languages=None,
                    date_of_birth=datetime.date(1980 + random.randint(0, 20), random.randint(1, 12), random.randint(1, 28)),
                    gender=random.choice(['male', 'female']),
                    phone=f"080{random.randint(10000000,99999999)}",
                    nin=nin,
                    hospital=hospital
                )
                # Doctor profile
                specialization = dept.name
                license_number = f"LIC-{dept.id}{i}{random.randint(1000,9999)}"
                license_expiry = timezone.now().date() + datetime.timedelta(days=365*random.randint(1, 5))
                years_exp = random.randint(3, 30)
                qualifications = random.choice(QUALIFICATIONS)
                # Assign surgical_subspecialty if department is surgical
                surgical_subspecialty = None
                if dept.department_type == 'surgical':
                    surgical_subspecialty = random.choice([s[0] for s in Doctor.SURGICAL_SUBSPECIALTIES])
                Doctor.objects.create(
                    user=user,
                    department=dept,
                    hospital=hospital,
                    specialization=specialization,
                    medical_license_number=license_number,
                    license_expiry_date=license_expiry,
                    years_of_experience=years_exp,
                    qualifications=qualifications,
                    board_certifications='FWACP',
                    is_active=True,
                    status='active',
                    available_for_appointments=True,
                    consultation_hours_start=datetime.time(8, 0),
                    consultation_hours_end=datetime.time(16, 0),
                    consultation_days='Mon,Tue,Wed,Thu,Fri',
                    max_daily_appointments=20,
                    appointment_duration=30,
                    languages_spoken=language_name,
                    medical_school='University of Ibadan',
                    graduation_year=2000 + random.randint(0, 20),
                    office_phone=f"01{random.randint(10000000,99999999)}",
                    office_location=f"Room {random.randint(100, 500)}",
                    emergency_contact=f"080{random.randint(10000000,99999999)}",
                    is_verified=True,
                    expertise_codes=['A00', 'B00'],
                    primary_expertise_codes=['A00'],
                    chronic_care_experience=random.choice([True, False]),
                    complex_case_rating=random.uniform(5, 10),
                    continuity_of_care_rating=random.uniform(5, 10),
                    surgical_subspecialty=surgical_subspecialty
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created doctor {first_name} {last_name} for {dept.name} in {hospital.name}'))
        self.stdout.write(self.style.SUCCESS(f'Total doctors created: {created_count}')) 