from django.core.management.base import BaseCommand
from api.models.medical.appointment import AppointmentType

class Command(BaseCommand):
    help = 'Creates default appointment types in the database'

    def handle(self, *args, **options):
        default_types = [
            {"id": "first_visit", "name": "First Visit"},
            {"id": "follow_up", "name": "Follow Up"},
            {"id": "consultation", "name": "Consultation"},
            {"id": "procedure", "name": "Procedure"},
            {"id": "test", "name": "Medical Test"},
            {"id": "vaccination", "name": "Vaccination"},
            {"id": "therapy", "name": "Therapy"}
        ]

        created_count = 0
        existing_count = 0

        for type_data in default_types:
            obj, created = AppointmentType.objects.get_or_create(
                id=type_data["id"],
                defaults={"name": type_data["name"]}
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created appointment type: {type_data['name']}"))
            else:
                existing_count += 1
                self.stdout.write(f"Appointment type already exists: {type_data['name']}")

        self.stdout.write(self.style.SUCCESS(
            f"Completed: {created_count} appointment types created, {existing_count} already existed."
        )) 