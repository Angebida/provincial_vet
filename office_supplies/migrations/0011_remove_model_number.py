from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('office_supplies', '0010_restore_unit_constraint'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='officesupply',
            name='model_number',
        ),
    ]
