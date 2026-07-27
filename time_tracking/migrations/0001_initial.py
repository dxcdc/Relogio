

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pim', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Nome')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descrição')),
                ('is_deleted', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nome do Projeto')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descrição')),
                ('is_deleted', models.BooleanField(default=False)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='time_tracking.customer', verbose_name='Cliente')),
            ],
            options={
                'verbose_name': 'Projeto',
                'verbose_name_plural': 'Projetos',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ProjectActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Atividade')),
                ('is_deleted', models.BooleanField(default=False)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='time_tracking.project', verbose_name='Projeto')),
            ],
            options={
                'verbose_name': 'Atividade do Projeto',
                'verbose_name_plural': 'Atividades do Projeto',
            },
        ),
        migrations.CreateModel(
            name='Timesheet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(verbose_name='Início da Semana')),
                ('end_date', models.DateField(verbose_name='Fim da Semana')),
                ('state', models.CharField(choices=[('NOT SUBMITTED', 'Não Enviado'), ('SUBMITTED', 'Enviado'), ('APPROVED', 'Aprovado'), ('REJECTED', 'Rejeitado')], default='NOT SUBMITTED', max_length=20, verbose_name='Status')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timesheets', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Timesheet',
                'verbose_name_plural': 'Timesheets',
                'ordering': ['-start_date'],
                'unique_together': {('employee', 'start_date')},
            },
        ),
        migrations.CreateModel(
            name='TimesheetActionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=50)),
                ('comment', models.TextField(blank=True, null=True)),
                ('performed_at', models.DateTimeField(auto_now_add=True)),
                ('performed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('timesheet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='action_logs', to='time_tracking.timesheet')),
            ],
            options={
                'verbose_name': 'Log de Ação',
                'ordering': ['performed_at'],
            },
        ),
        migrations.CreateModel(
            name='ProjectAdmin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pim.employee')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admins', to='time_tracking.project')),
            ],
            options={
                'verbose_name': 'Admin do Projeto',
                'unique_together': {('project', 'employee')},
            },
        ),
        migrations.CreateModel(
            name='TimesheetItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Data')),
                ('duration', models.TimeField(default='00:00', verbose_name='Horas')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('activity', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='time_tracking.projectactivity', verbose_name='Atividade')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='time_tracking.project', verbose_name='Projeto')),
                ('timesheet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='time_tracking.timesheet')),
            ],
            options={
                'verbose_name': 'Item de Timesheet',
                'verbose_name_plural': 'Itens de Timesheet',
                'unique_together': {('timesheet', 'project', 'activity', 'date')},
            },
        ),
    ]
