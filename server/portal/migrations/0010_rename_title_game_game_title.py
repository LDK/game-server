# Generated by Django 5.0 on 2024-09-15 07:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0009_remove_game_players_gameplayer_game_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='game',
            old_name='title',
            new_name='game_title',
        ),
    ]
