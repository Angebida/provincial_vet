from django.db import migrations, models
import django.db.models.deletion

def link_units(apps, schema_editor):
    VeterinarySupply = apps.get_model('vet_supplies', 'VeterinarySupply')
    UnitMeasure = apps.get_model('inventory', 'UnitMeasure')
    
    for supply in VeterinarySupply.objects.all():
        try:
            # Convert unit name to match UnitMeasure names
            unit_name = supply.unit.lower().strip()
            unit_obj = UnitMeasure.objects.get(name=unit_name)
            supply.unit_new = unit_obj
            supply.save()
        except UnitMeasure.DoesNotExist:
            print(f"Warning: Unit {unit_name} not found for {supply.name}")
            # Create missing unit if needed
            unit_obj = UnitMeasure.objects.create(
                name=unit_name,
                display_name=supply.unit.title(),
                is_active=True,
                order=99
            )
            supply.unit_new = unit_obj
            supply.save()

def reverse_link(apps, schema_editor):
    VeterinarySupply = apps.get_model('vet_supplies', 'VeterinarySupply')
    for supply in VeterinarySupply.objects.all():
        old_unit = supply.unit_new.name if supply.unit_new else 'units'
        supply.unit = old_unit
        supply.save()

class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0001_initial'),
        ('vet_supplies', '0008_convert_unit_data'),
    ]

    operations = [
        # Add new FK field while keeping old field
        migrations.AddField(
            model_name='veterinarysupply',
            name='unit_new',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='vet_supplies',
                to='inventory.unitmeasure'
            ),
        ),
        # Convert the data
        migrations.RunPython(link_units, reverse_link),
        # Remove old field 
        migrations.RemoveField(
            model_name='veterinarysupply',
            name='unit',
        ),
        # Rename new field to unit
        migrations.RenameField(
            model_name='veterinarysupply',
            old_name='unit_new',
            new_name='unit',
        ),
        # Make the field required
        migrations.AlterField(
            model_name='veterinarysupply',
            name='unit',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='vet_supplies',
                to='inventory.unitmeasure'
            ),
        ),
    ]
