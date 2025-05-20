from django.db import migrations, models
import django.db.models.deletion

def link_units(apps, schema_editor):
    OfficeSupply = apps.get_model('office_supplies', 'OfficeSupply')
    UnitMeasure = apps.get_model('inventory', 'UnitMeasure')
    
    for supply in OfficeSupply.objects.all():
        if supply.unit_temp:
            try:
                unit_obj = UnitMeasure.objects.get(name=supply.unit_temp.lower())
                supply.unit = unit_obj
                supply.save()
            except UnitMeasure.DoesNotExist:
                print(f"Warning: Unit {supply.unit_temp} not found for {supply.name}")
                # Create missing unit if needed
                unit_obj = UnitMeasure.objects.create(
                    name=supply.unit_temp.lower(),
                    display_name=supply.unit_temp.title(),
                    is_active=True,
                    order=99
                )
                supply.unit = unit_obj
                supply.save()

class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0001_initial'),
        ('office_supplies', '0009_convert_unit_data'),
    ]

    operations = [
        # Add new FK field
        migrations.AddField(
            model_name='officesupply',
            name='unit',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='office_supplies',
                to='inventory.unitmeasure'
            ),
        ),
        # Link the units
        migrations.RunPython(link_units),
        # Make unit required
        migrations.AlterField(
            model_name='officesupply',
            name='unit',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='office_supplies',
                to='inventory.unitmeasure'
            ),
        ),
        # Remove temporary field
        migrations.RemoveField(
            model_name='officesupply',
            name='unit_temp',
        ),
    ]
