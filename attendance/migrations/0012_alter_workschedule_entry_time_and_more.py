

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0011_alter_shiftswaprequest_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workschedule',
            name='entry_time',
            field=models.TimeField(blank=True, null=True, verbose_name='(Legado) Horário de Entrada'),
        ),
        migrations.AlterField(
            model_name='workschedule',
            name='exit_time',
            field=models.TimeField(blank=True, null=True, verbose_name='(Legado) Horário de Saída'),
        ),
        migrations.AlterField(
            model_name='workschedule',
            name='lunch_end',
            field=models.TimeField(blank=True, null=True, verbose_name='(Legado) Fim do Almoço'),
        ),
        migrations.AlterField(
            model_name='workschedule',
            name='lunch_start',
            field=models.TimeField(blank=True, null=True, verbose_name='(Legado) Início do Almoço'),
        ),
        migrations.AlterField(
            model_name='workschedule',
            name='saturday_entry_time',
            field=models.TimeField(blank=True, null=True, verbose_name='(Legado) Entrada no Sábado'),
        ),
        migrations.AlterField(
            model_name='workschedule',
            name='saturday_exit_time',
            field=models.TimeField(blank=True, null=True, verbose_name='(Legado) Saída no Sábado'),
        ),
        migrations.AlterField(
            model_name='workschedule',
            name='work_days',
            field=models.CharField(blank=True, default='0,1,2,3,4', max_length=20, null=True, verbose_name='(Legado) Dias de Trabalho'),
        ),
        migrations.CreateModel(
            name='WorkScheduleDay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.IntegerField(verbose_name='Dia da Semana')),
                ('is_work_day', models.BooleanField(default=True, verbose_name='Dia de Trabalho')),
                ('entry_time', models.TimeField(blank=True, null=True, verbose_name='Horário de Entrada')),
                ('exit_time', models.TimeField(blank=True, null=True, verbose_name='Horário de Saída')),
                ('lunch_start', models.TimeField(blank=True, null=True, verbose_name='Início do Almoço')),
                ('lunch_end', models.TimeField(blank=True, null=True, verbose_name='Fim do Almoço')),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='days', to='attendance.workschedule')),
            ],
            options={
                'ordering': ['weekday'],
                'unique_together': {('schedule', 'weekday')},
            },
        ),
    ]
