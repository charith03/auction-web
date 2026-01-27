from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auction', '0007_player_age_player_bowling_player_hand'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='sold_status',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='room',
            name='sold_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='room',
            name='sold_team',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='room',
            name='sold_price',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
