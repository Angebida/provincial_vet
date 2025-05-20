from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0004_merge_user_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventorymovement',
            name='user',
        ),
    ]
