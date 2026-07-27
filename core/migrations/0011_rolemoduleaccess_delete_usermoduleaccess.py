

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_usermoduleaccess'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoleModuleAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('Admin', 'Administrador'), ('HR', 'Recursos Humanos (RH)'), ('ESS', 'Funcionário (ESS)'), ('Supervisor', 'Supervisor')], max_length=20, unique=True, verbose_name='Tipo de Usuário')),
                ('netgram', models.BooleanField(default=True, verbose_name='Módulo Netgram')),
                ('org_chart', models.BooleanField(default=True, verbose_name='Módulo Organograma')),
                ('attendance', models.BooleanField(default=True, verbose_name='Meus Registros de Ponto')),
                ('leave', models.BooleanField(default=True, verbose_name='Férias/Ausências')),
                ('swap', models.BooleanField(default=True, verbose_name='Módulo de Trocas DSR')),
                ('claim', models.BooleanField(default=True, verbose_name='Reembolsos/Despesas')),
                ('performance', models.BooleanField(default=True, verbose_name='Desempenho/Avaliações')),
            ],
            options={
                'verbose_name': 'Controle de Módulo por Cargo',
                'verbose_name_plural': 'Controles de Módulos por Cargo',
            },
        ),
        migrations.DeleteModel(
            name='UserModuleAccess',
        ),
    ]
