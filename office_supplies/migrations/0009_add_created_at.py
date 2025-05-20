from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [
        ('office_supplies', '0008_alter_officesupply_unit'),
        ('inventory', '0001_initial'),  # Add inventory dependency
    ]

    operations = [
        migrations.AddField(
            model_name='officesupply',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
