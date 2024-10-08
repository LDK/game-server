# Generated by Django 5.0 on 2024-09-15 19:47

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0011_rename_title_gameplayer_game_title'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='game_title',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='portal.gametitle'),
        ),
        migrations.AlterField(
            model_name='game',
            name='starter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='game',
            name='winner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='winner', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='gameplayer',
            name='game',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='portal.game'),
        ),
        migrations.AlterField(
            model_name='gameplayer',
            name='game_title',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='portal.gametitle'),
        ),
        migrations.AlterField(
            model_name='gameplayer',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
    ]
