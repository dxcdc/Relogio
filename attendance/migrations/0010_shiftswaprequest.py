

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0009_add_shift_overrides'),
        ('pim', '0004_orghierarchyrequest'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ShiftSwapRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Data da Troca')),
                ('reason', models.TextField(blank=True, verbose_name='Motivo')),
                ('status', models.CharField(choices=[('PENDING', 'Pendente'), ('APPROVED', 'Aprovado'), ('REJECTED', 'Rejeitado')], default='PENDING', max_length=20, verbose_name='Status')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='swap_requests_made', to='pim.employee', verbose_name='Solicitante')),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Resolvido por')),
                ('target_employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='swap_requests_received', to='pim.employee', verbose_name='Colega Alvo')),
            ],
            options={
                'verbose_name': 'Solicitação de Troca de Turno',
                'verbose_name_plural': 'Solicitações de Troca de Turno',
                'ordering': ['-created_at'],
            },
        ),
    ]
