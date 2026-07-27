

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0007_add_saturday_override_times'),
        ('pim', '0003_employee_legal_entity'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShiftPattern',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nome do Padrão')),
                ('pattern_type', models.CharField(choices=[('WEEKLY', 'Padrão Semanal'), ('FREE', 'Padrão Livre')], max_length=10, verbose_name='Tipo')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Padrão de Turno',
                'verbose_name_plural': 'Padrões de Turno',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='EmployeeShiftAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(verbose_name='Data de Início do Ciclo')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='Data de Fim (opcional)')),
                ('notes', models.TextField(blank=True, verbose_name='Observações')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shift_assignments', to='pim.employee', verbose_name='Funcionário')),
                ('pattern', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='assignments', to='attendance.shiftpattern', verbose_name='Padrão de Turno')),
            ],
            options={
                'verbose_name': 'Atribuição de Turno',
                'verbose_name_plural': 'Atribuições de Turno',
                'ordering': ['-start_date'],
            },
        ),
        migrations.CreateModel(
            name='ShiftPatternDay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(verbose_name='Posição no Ciclo')),
                ('is_work_day', models.BooleanField(default=True, verbose_name='Dia de Trabalho')),
                ('entry_time', models.TimeField(blank=True, null=True, verbose_name='Entrada')),
                ('exit_time', models.TimeField(blank=True, null=True, verbose_name='Saída')),
                ('pattern', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='days', to='attendance.shiftpattern')),
            ],
            options={
                'verbose_name': 'Dia do Padrão',
                'verbose_name_plural': 'Dias do Padrão',
                'ordering': ['position'],
                'unique_together': {('pattern', 'position')},
            },
        ),
    ]
