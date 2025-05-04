from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0009_medicalrecordaccess'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='medical_record_otp',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='medical_record_otp_created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='medical_record_access_token',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='medical_record_token_created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ] 