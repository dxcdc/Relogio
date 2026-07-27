

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0002_legalentity'),
        ('core', '0006_passwordresettoken'),
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Título')),
                ('content', models.TextField(verbose_name='Conteúdo do Aviso')),
                ('image', models.ImageField(blank=True, null=True, upload_to='announcements/', verbose_name='Foto/Capa (Opcional)')),
                ('visibility', models.CharField(choices=[('ALL', 'Toda a Empresa (Público Geral)'), ('DEPARTMENT_ONLY', 'Apenas Departamento/Filial')], default='ALL', max_length=20, verbose_name='Visibilidade')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Autor')),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='admin_app.subunit', verbose_name='Departamento Restrito')),
            ],
            options={
                'verbose_name': 'Mural de Aviso',
                'verbose_name_plural': 'Mural de Avisos',
                'ordering': ['-created_at'],
            },
        ),
    ]
