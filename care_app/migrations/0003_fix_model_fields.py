# Generated manually to fix model field issues

import django.utils.timezone
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('care_app', '0002_remove_vitalslog_blood_pressure_and_more'),
    ]

    operations = [
        # Fix ElderProfile timestamp fields
        migrations.AlterField(
            model_name='elderprofile',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='elderprofile',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        # Rename log_date to recorded_at in VitalsLog
        migrations.RenameField(
            model_name='vitalslog',
            old_name='log_date',
            new_name='recorded_at',
        ),
    ]
