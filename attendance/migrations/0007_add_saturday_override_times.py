

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0006_add_work_days_to_schedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='workschedule',
            name='saturday_entry_time',
            field=models.TimeField(blank=True, null=True, verbose_name='Entrada no Sábado'),
        ),
        migrations.AddField(
            model_name='workschedule',
            name='saturday_exit_time',
            field=models.TimeField(blank=True, null=True, verbose_name='Saída no Sábado'),
        ),
    ]
