from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('office_supplies', '0004_remove_officesupply_supplier'),
    ]

    operations = [
        migrations.AddField(
            model_name='officesupply',
            name='expiration_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
