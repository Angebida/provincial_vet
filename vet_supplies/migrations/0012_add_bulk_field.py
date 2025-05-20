from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('vet_supplies', '0011_remove_batch_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='veterinarysupplyrequest',
            name='is_bulk',
            field=models.BooleanField(default=False, verbose_name='Bulk Request'),
        ),
    ]
