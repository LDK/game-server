# Generated by Django 5.0 on 2024-04-26 03:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('date_created', models.DateField(auto_now_add=True)),
                ('date_started', models.DateField(blank=True, null=True)),
                ('date_finished', models.DateField(blank=True, null=True)),
                ('cpu_winner', models.TextField(blank=True, null=True)),
                ('last_move', models.JSONField(blank=True, null=True)),
                ('last_move_ts', models.DateTimeField(blank=True, null=True)),
                ('specifics', models.JSONField(blank=True, null=True)),
                ('starter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('title_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portal.gametitle')),
                ('turn', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='turn', to=settings.AUTH_USER_MODEL)),
                ('winner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='winner', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GamePlayer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('starter', models.BooleanField(default=False)),
                ('order', models.SmallIntegerField()),
                ('date_joined', models.DateField(auto_now_add=True)),
                ('date_left', models.DateField(blank=True, null=True)),
                ('cpu_name', models.CharField(blank=True, max_length=100, null=True)),
                ('specifics', models.JSONField(blank=True, null=True)),
                ('gameId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portal.game')),
                ('title', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portal.gametitle')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('gameId', 'order')},
            },
        ),
    ]
