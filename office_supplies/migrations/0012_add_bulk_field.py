from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('office_supplies', '0011_remove_model_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='officesupplyrequest',
            name='is_bulk',
            field=models.BooleanField(default=False, verbose_name='Bulk Request'),
        ),
    ]
