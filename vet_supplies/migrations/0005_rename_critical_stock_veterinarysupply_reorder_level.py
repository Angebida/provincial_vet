from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vet_supplies', '0004_alter_veterinarysupply_unit'),
    ]

    operations = [
        migrations.RenameField(
            model_name='veterinarysupply',
            old_name='critical_stock',
            new_name='reorder_level',
        ),
    ]
