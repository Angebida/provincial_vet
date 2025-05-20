from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('vet_supplies', '0005_rename_critical_stock_veterinarysupply_reorder_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='veterinarysupply',
            name='expiration_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
