

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_announcement_buzz_post_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserModuleAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('netgram', models.BooleanField(default=True, verbose_name='Módulo Netgram')),
                ('org_chart', models.BooleanField(default=True, verbose_name='Módulo Organograma')),
                ('attendance', models.BooleanField(default=True, verbose_name='Meus Registros de Ponto')),
                ('leave', models.BooleanField(default=True, verbose_name='Módulo Férias/Ausências')),
                ('swap', models.BooleanField(default=True, verbose_name='Módulo de Trocas DSR')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='module_access', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Controle de Módulo',
                'verbose_name_plural': 'Controles de Módulos',
            },
        ),
    ]
