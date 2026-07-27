

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0012_alter_workschedule_entry_time_and_more'),
        ('pim', '0004_orghierarchyrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendanceadjustment',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pendente'), ('SUPERVISOR_APPROVED', 'Ag. RH'), ('APPROVED', 'Aprovado'), ('REJECTED', 'Rejeitado')], default='PENDING', max_length=20),
        ),
        migrations.CreateModel(
            name='WorkScheduleAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(default=django.utils.timezone.now, verbose_name='Data de Início')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='Data de Fim')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedule_assignments', to='pim.employee', verbose_name='Funcionário')),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='attendance.workschedule', verbose_name='Escala de Trabalho')),
            ],
            options={
                'verbose_name': 'Designação de Escala',
                'verbose_name_plural': 'Designações de Escalas',
                'ordering': ['-start_date'],
            },
        ),
    ]
