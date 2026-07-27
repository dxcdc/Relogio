

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0002_legalentity'),
        ('pim', '0003_employee_legal_entity'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OrgHierarchyRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', 'Pendente'), ('APPROVED', 'Aprovado'), ('REJECTED', 'Rejeitado')], default='PENDING', max_length=20, verbose_name='Status')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('resolved_at', models.DateTimeField(blank=True, null=True, verbose_name='Resolvido em')),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='org_requests_made', to='pim.employee', verbose_name='Solicitante')),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_org_requests', to=settings.AUTH_USER_MODEL, verbose_name='Resolvido Por')),
                ('supervisor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming_org_requests', to='pim.employee', verbose_name='Novo Supervisor')),
                ('target_department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='admin_app.subunit', verbose_name='Setor Alvo')),
                ('target_employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='org_hierarchy_changes', to='pim.employee', verbose_name='Funcionário Alvo')),
            ],
            options={
                'verbose_name': 'Solicitação de Organograma',
                'verbose_name_plural': 'Solicitações de Organograma',
                'ordering': ['-created_at'],
            },
        ),
    ]
