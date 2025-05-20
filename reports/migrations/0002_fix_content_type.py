from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorymovement',
            name='content_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, 
                to='contenttypes.contenttype',
                db_constraint=False  # Temporarily disable constraint
            ),
        ),
        # Re-enable constraint after data is fixed
        migrations.AlterField(
            model_name='inventorymovement',
            name='content_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='contenttypes.contenttype'
            ),
        ),
    ]
