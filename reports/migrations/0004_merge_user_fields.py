from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('reports', '0003_inventorymovement_unit_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventorymovement',
            name='user',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='inventory_movements',
                to='users.customuser'
            ),
        ),
    ]
