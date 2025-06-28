# Generated migration for simplified clinical guidelines file handling

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_clinical_guidelines'),
    ]

    operations = [
        # The file_path field was already added in the original model,
        # so no changes are needed to the database schema.
        # This migration serves as a marker for the simplification of file handling.
    ]