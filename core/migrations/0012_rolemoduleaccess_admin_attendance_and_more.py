

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_rolemoduleaccess_delete_usermoduleaccess'),
    ]

    operations = [
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='admin_attendance',
            field=models.BooleanField(default=True, verbose_name='Admin: Escalas e Fechamento'),
        ),
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='admin_core',
            field=models.BooleanField(default=True, verbose_name='Admin: Matastros Base'),
        ),
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='audit',
            field=models.BooleanField(default=True, verbose_name='Log de Auditoria'),
        ),
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='endpoints',
            field=models.BooleanField(default=True, verbose_name='Endpoints API'),
        ),
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='team_approvals',
            field=models.BooleanField(default=True, verbose_name='Equipe: Central de Aprovações'),
        ),
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='team_attendance',
            field=models.BooleanField(default=True, verbose_name='Equipe: Ponto/Relatórios'),
        ),
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='team_employees',
            field=models.BooleanField(default=True, verbose_name='Equipe: Funcionários'),
        ),
    ]
