

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0017_pending_punch_request'),
        ('pim', '0004_orghierarchyrequest'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AttendanceClosingSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(default='Empresa Padrão', max_length=100, verbose_name='Empresa')),
                ('payroll_closing_day', models.PositiveIntegerField(default=30, verbose_name='Dia de Fechamento da Folha')),
                ('hour_bank_closing_months', models.PositiveIntegerField(default=6, verbose_name='Ciclo do Banco de Horas (Meses)')),
                ('night_shift_start', models.TimeField(default='22:00:00', verbose_name='Início Adicional Noturno')),
                ('night_shift_end', models.TimeField(default='05:00:00', verbose_name='Fim Adicional Noturno')),
            ],
            options={
                'verbose_name': 'Configuração de Ponto',
                'verbose_name_plural': 'Configurações de Ponto',
            },
        ),
        migrations.CreateModel(
            name='DailyTimeBalance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('theo_minutes', models.IntegerField(default=0, verbose_name='Horas Teóricas')),
                ('acted_minutes', models.IntegerField(default=0, verbose_name='Horas Trabalhadas')),
                ('regular_minutes', models.IntegerField(default=0, verbose_name='Horas Normais')),
                ('extra_50_minutes', models.IntegerField(default=0, verbose_name='HE 50%')),
                ('extra_100_minutes', models.IntegerField(default=0, verbose_name='HE 100%')),
                ('night_minutes', models.IntegerField(default=0, verbose_name='Horas Noturnas')),
                ('negative_minutes', models.IntegerField(default=0, verbose_name='Atraso/Saída Antecipada')),
                ('processed_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_balances', to='pim.employee')),
                ('record', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='attendance.attendancerecord')),
            ],
            options={
                'verbose_name': 'Saldo Diário de Ponto',
                'verbose_name_plural': 'Saldos Diários de Ponto',
                'unique_together': {('employee', 'date')},
            },
        ),
        migrations.CreateModel(
            name='TimesheetPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(verbose_name='Data de Início')),
                ('end_date', models.DateField(verbose_name='Data de Fim')),
                ('status', models.CharField(choices=[('OPEN', 'Aberto'), ('LOCKED', 'Em Análise'), ('CLOSED', 'Fechado/Pago')], default='OPEN', max_length=10)),
                ('total_regular_minutes', models.IntegerField(default=0)),
                ('total_extra_50_minutes', models.IntegerField(default=0)),
                ('total_extra_100_minutes', models.IntegerField(default=0)),
                ('total_night_minutes', models.IntegerField(default=0)),
                ('total_negative_minutes', models.IntegerField(default=0)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('closed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_periods', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Espelho de Ponto',
                'verbose_name_plural': 'Espelhos de Ponto',
                'unique_together': {('employee', 'start_date', 'end_date')},
            },
        ),
    ]
