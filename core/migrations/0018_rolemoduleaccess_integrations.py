

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_rolemoduleaccess_attendance_block_early_punch_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='integrations',
            field=models.BooleanField(default=True, verbose_name='Integrações & API (Em Construção)'),
        ),
    ]
