from django.db import migrations, models

def create_units(apps, schema_editor):
    UnitMeasure = apps.get_model('inventory', 'UnitMeasure')
    
    default_units = [
        ('units', 'Units'),
        ('boxes', 'Boxes'),
        ('bottles', 'Bottles'),
        ('vials', 'Vials'),
        ('sachets', 'Sachets'),
        ('pcs', 'Pieces'),
        ('tablets', 'Tablets'),
        ('ampoules', 'Ampoules'),
        ('doses', 'Doses')
    ]

    for unit_name, display_name in default_units:
        UnitMeasure.objects.get_or_create(
            name=unit_name,
            defaults={
                'display_name': display_name,
                'is_active': True,
                'order': 99
            }
        )

def reverse_units(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('vet_supplies', '0007_alter_veterinarysupply_unit'),
        ('inventory', '0001_initial'),
    ]

    operations = [
        # First remove the foreign key constraint
        migrations.AlterField(
            model_name='veterinarysupply',
            name='unit',
            field=models.CharField(max_length=50),
        ),
        # Create unit measures
        migrations.RunPython(create_units, reverse_units),
    ]
