

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0003_workschedule'),
        ('pim', '0002_employee_work_schedule'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AttendanceAdjustment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Data do Ajuste')),
                ('punch_in', models.TimeField(blank=True, null=True, verbose_name='Entrada Solicitada')),
                ('punch_out', models.TimeField(blank=True, null=True, verbose_name='Saída Solicitada')),
                ('reason', models.TextField(verbose_name='Motivo do Ajuste')),
                ('status', models.CharField(choices=[('PENDING', 'Pendente'), ('APPROVED', 'Aprovado'), ('REJECTED', 'Rejeitado')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('attendance_record', models.ForeignKey(blank=True, help_text='Se for ajuste de um registro existente.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='adjustments', to='attendance.attendancerecord')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_adjustments', to='pim.employee')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_adjustments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Solicitação de Ajuste de Ponto',
                'verbose_name_plural': 'Solicitações de Ajuste de Ponto',
                'ordering': ['-created_at'],
            },
        ),
    ]
