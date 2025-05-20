from django.db import migrations, models

def create_default_units(apps, schema_editor):
    UnitMeasure = apps.get_model('inventory', 'UnitMeasure')
    default_units = [
        ('units', 'Units', 1),
        ('boxes', 'Boxes', 2),
        ('bottles', 'Bottles', 3),
        ('vials', 'Vials', 4),
        ('sachets', 'Sachets', 5),
        ('pcs', 'Pieces', 6),
        ('tablets', 'Tablets', 7),
        ('ampoules', 'Ampoules', 8),
        ('doses', 'Doses', 9),
        ('reams', 'Reams', 10),
        ('sets', 'Sets', 11),
        ('packs', 'Packs', 12),
        ('rolls', 'Rolls', 13),
        ('cartridges', 'Cartridges', 14)
    ]
    
    for name, display_name, order in default_units:
        UnitMeasure.objects.create(
            name=name,
            display_name=display_name,
            order=order,
            is_active=True
        )

class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='UnitMeasure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('display_name', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['order', 'display_name'],
            },
        ),
        migrations.RunPython(create_default_units, migrations.RunPython.noop),
    ]
