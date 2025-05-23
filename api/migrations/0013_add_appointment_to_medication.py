from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_remove_appointment_medical_summary_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='medication',
            name='appointment',
            field=models.ForeignKey(blank=True, help_text='Appointment during which this medication was prescribed', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='medications', to='api.appointment'),
        ),
    ] 