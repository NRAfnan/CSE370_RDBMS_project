# Generated manually to add audit fields to EmergencyContact

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def set_default_timestamps(apps, schema_editor):
    """Set default timestamps for existing emergency contacts"""
    EmergencyContact = apps.get_model('care_app', 'EmergencyContact')
    now = django.utils.timezone.now()
    EmergencyContact.objects.filter(created_at__isnull=True).update(created_at=now)


class Migration(migrations.Migration):

    dependencies = [
        ('care_app', '0004_alter_elderprofile_created_at'),
    ]

    operations = [
        # First, add the new fields as nullable
        migrations.AddField(
            model_name='emergencycontact',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='emergencycontact',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_emergency_contacts', to='auth.user'),
        ),
        migrations.AddField(
            model_name='emergencycontact',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_emergency_contacts', to='auth.user'),
        ),
        
        # Set default timestamps for existing records
        migrations.RunPython(set_default_timestamps),
        
        # Now make created_at non-nullable with auto_now_add
        migrations.AlterField(
            model_name='emergencycontact',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        
        # Add Meta ordering
        migrations.AlterModelOptions(
            name='emergencycontact',
            options={'ordering': ['-is_primary', 'name']},
        ),
    ]
