from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('vet_supplies', '0010_merge_20250507_1534'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='veterinarysupply',
            name='batch_number',
        ),
    ]
