from django.db import migrations, models
import django.db.models.deletion

def convert_units(apps, schema_editor):
    OfficeSupply = apps.get_model('office_supplies', 'OfficeSupply')
    UnitMeasure = apps.get_model('inventory', 'UnitMeasure')
    
    # First store all existing unit values in unit_temp
    supplies = OfficeSupply.objects.all()
    for supply in supplies:
        unit_name = supply.unit if isinstance(supply.unit, str) else str(supply.unit)
        supply.unit_temp = unit_name.lower()
        supply.save()

def reverse_convert(apps, schema_editor):
    OfficeSupply = apps.get_model('office_supplies', 'OfficeSupply') 
    supplies = OfficeSupply.objects.all()
    for supply in supplies:
        supply.unit = supply.unit_temp
        supply.save()

class Migration(migrations.Migration):
    dependencies = [
        ('office_supplies', '0008_alter_officesupply_unit'),
        ('inventory', '0001_initial'),
    ]

    operations = [
        # First add a temporary column
        migrations.AddField(
            model_name='officesupply',
            name='unit_temp',
            field=models.CharField(max_length=50, null=True),
        ),
        # Store current unit values
        migrations.RunPython(convert_units, reverse_convert),
        # Remove the old unit field
        migrations.RemoveField(
            model_name='officesupply',
            name='unit',
        ),
    ]
