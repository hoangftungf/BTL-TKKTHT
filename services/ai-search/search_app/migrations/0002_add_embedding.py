from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('search_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='productindex',
            name='embedding',
            field=models.BinaryField(blank=True, null=True),
        ),
    ]
