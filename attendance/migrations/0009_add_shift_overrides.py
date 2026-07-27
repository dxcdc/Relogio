

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0008_add_shift_patterns'),
        ('pim', '0003_employee_legal_entity'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ShiftOverride',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Data da Exceção')),
                ('override_type', models.CharField(choices=[('WORK', 'Dia de Trabalho'), ('REST', 'Dia de Folga')], max_length=10, verbose_name='Tipo de Exceção')),
                ('entry_time', models.TimeField(blank=True, null=True, verbose_name='Entrada')),
                ('exit_time', models.TimeField(blank=True, null=True, verbose_name='Saída')),
                ('reason', models.CharField(blank=True, max_length=200, verbose_name='Motivo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shift_overrides', to='pim.employee', verbose_name='Funcionário')),
            ],
            options={
                'verbose_name': 'Exceção de Turno',
                'verbose_name_plural': 'Exceções de Turno',
                'ordering': ['-date'],
                'unique_together': {('employee', 'date')},
            },
        ),
    ]
