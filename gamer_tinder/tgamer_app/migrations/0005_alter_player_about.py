# Generated by Django 4.0.4 on 2022-04-25 22:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgamer_app', '0004_rename_steam_nickname_player_steam_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='about',
            field=models.CharField(max_length=4096, verbose_name='О себе'),
        ),
    ]