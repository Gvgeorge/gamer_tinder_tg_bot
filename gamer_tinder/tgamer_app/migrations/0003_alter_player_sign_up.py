# Generated by Django 4.0.4 on 2022-04-24 03:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgamer_app', '0002_rename_telegram_id_player_tg_id_alter_player_sign_up'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='sign_up',
            field=models.IntegerField(choices=[(0, 'New Player'), (1, 'Steam Name'), (2, 'About'), (3, 'Prefered Game'), (4, 'Done')], default=0),
        ),
    ]
