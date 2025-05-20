from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [
        ('vet_supplies', '0013_requestitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='veterinarysupply',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
