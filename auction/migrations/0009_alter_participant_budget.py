from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auction', '0008_room_sold_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='budget',
            field=models.DecimalField(decimal_places=2, default=120.0, max_digits=6),
        ),
    ]
