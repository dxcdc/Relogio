

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('admin_app', '0001_initial'),
        ('pim', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nome do Feriado')),
                ('date', models.DateField(verbose_name='Data')),
                ('recurring', models.BooleanField(default=False, verbose_name='Recorrente (Anual)')),
                ('length', models.IntegerField(choices=[(0, 'Dia Inteiro'), (4, 'Meio Período')], default=0, verbose_name='Duração')),
            ],
            options={
                'verbose_name': 'Feriado',
                'verbose_name_plural': 'Feriados',
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='LeaveEntitlementType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nome')),
                ('is_editable', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Tipo de Direito',
            },
        ),
        migrations.CreateModel(
            name='WorkWeek',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.IntegerField(choices=[(0, 'Segunda'), (1, 'Terça'), (2, 'Quarta'), (3, 'Quinta'), (4, 'Sexta'), (5, 'Sábado'), (6, 'Domingo')], unique=True, verbose_name='Dia')),
                ('day_type', models.CharField(choices=[('working_day', 'Dia de Trabalho'), ('non_working_day', 'Folga'), ('half_day', 'Meio Período')], default='working_day', max_length=20, verbose_name='Tipo')),
            ],
            options={
                'verbose_name': 'Semana de Trabalho',
                'ordering': ['day'],
            },
        ),
        migrations.CreateModel(
            name='LeaveRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_applied', models.DateField(default=django.utils.timezone.now, verbose_name='Data da Solicitação')),
                ('from_date', models.DateField(verbose_name='De')),
                ('to_date', models.DateField(verbose_name='Até')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Comentário')),
                ('status', models.CharField(choices=[('PENDING', 'Pendente'), ('APPROVED', 'Aprovada'), ('REJECTED', 'Rejeitada'), ('CANCELLED', 'Cancelada'), ('REQUESTED_MORE_INFO', 'Aguardando Informações')], default='PENDING', max_length=30, verbose_name='Status')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_requests', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Solicitação de Licença',
                'verbose_name_plural': 'Solicitações de Licença',
                'ordering': ['-date_applied'],
            },
        ),
        migrations.CreateModel(
            name='LeaveRequestComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('comment', models.TextField(verbose_name='Comentário')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('leave_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='leave.leaverequest')),
            ],
            options={
                'verbose_name': 'Comentário',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='LeaveType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Tipo de Licença')),
                ('is_deleted', models.BooleanField(default=False)),
                ('leave_type_applicable_all', models.BooleanField(default=True)),
                ('operational_country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.country')),
            ],
            options={
                'verbose_name': 'Tipo de Licença',
                'verbose_name_plural': 'Tipos de Licença',
            },
        ),
        migrations.AddField(
            model_name='leaverequest',
            name='leave_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='leave.leavetype', verbose_name='Tipo de Licença'),
        ),
        migrations.CreateModel(
            name='LeavePeriodHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateField(auto_now_add=True)),
                ('start_month', models.IntegerField(default=1)),
                ('start_day', models.IntegerField(default=1)),
                ('leave_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='leave.leavetype')),
            ],
            options={
                'verbose_name': 'Período de Licença',
            },
        ),
        migrations.CreateModel(
            name='LeaveEntitlement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_date', models.DateField(verbose_name='De')),
                ('to_date', models.DateField(verbose_name='Até')),
                ('no_of_days', models.DecimalField(decimal_places=2, default=0, max_digits=7, verbose_name='Dias')),
                ('days_used', models.DecimalField(decimal_places=2, default=0, max_digits=7, verbose_name='Dias Usados')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_entitlements', to='pim.employee')),
                ('entitlement_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='leave.leaveentitlementtype')),
                ('leave_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='leave.leavetype', verbose_name='Tipo')),
            ],
            options={
                'verbose_name': 'Direito de Licença',
                'verbose_name_plural': 'Direitos de Licença',
            },
        ),
        migrations.CreateModel(
            name='Leave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Data')),
                ('status', models.CharField(choices=[('PENDING', 'Pendente'), ('APPROVED', 'Aprovada'), ('REJECTED', 'Rejeitada'), ('CANCELLED', 'Cancelada')], default='PENDING', max_length=30)),
                ('duration_type', models.IntegerField(choices=[(0, 'Dia Inteiro'), (4, 'Meio Período')], default=0)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pim.employee')),
                ('leave_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leaves', to='leave.leaverequest')),
                ('leave_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='leave.leavetype')),
            ],
            options={
                'verbose_name': 'Licença',
                'verbose_name_plural': 'Licenças',
                'ordering': ['date'],
            },
        ),
    ]
