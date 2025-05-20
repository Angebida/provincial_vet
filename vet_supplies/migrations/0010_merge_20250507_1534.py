from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('vet_supplies', '0006_alter_veterinarysupply_expiration_date'),
        ('vet_supplies', '0009_restore_unit_constraint'),
    ]

    operations = [
        # No operations needed, just merging branches
    ]
