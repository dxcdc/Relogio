

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_orangeuser_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('LOGIN', 'Login'), ('LEAVE_APPROVE', 'Licença Aprovada'), ('LEAVE_REJECT', 'Licença Rejeitada'), ('ADJ_APPROVE', 'Ajuste Aprovado'), ('ADJ_REJECT', 'Ajuste Rejeitado'), ('EMP_CREATE', 'Funcionário Criado'), ('EMP_TERMINATE', 'Funcionário Desligado'), ('USER_CREATE', 'Usuário Criado'), ('USER_EDIT', 'Usuário Editado'), ('OTHER', 'Outro')], default='OTHER', max_length=30)),
                ('description', models.TextField(blank=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Log de Auditoria',
                'verbose_name_plural': 'Logs de Auditoria',
                'ordering': ['-created_at'],
            },
        ),
    ]
