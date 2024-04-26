from django.db import migrations

def load_fixture(apps, schema_editor):
    from django.core.management import call_command
    call_command('loaddata', 'gametitles1.json')

class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0003_rename_title_id_game_title'),
    ]

    operations = [
        migrations.RunPython(load_fixture),
    ]
