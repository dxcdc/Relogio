

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0003_workschedule'),
        ('pim', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='work_schedule',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employees', to='attendance.workschedule', verbose_name='Escala de Trabalho'),
        ),
    ]
