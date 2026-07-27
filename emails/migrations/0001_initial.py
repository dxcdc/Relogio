

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmailConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('backend', models.CharField(default='django.core.mail.backends.smtp.EmailBackend', max_length=100, verbose_name='Email Backend')),
                ('host', models.CharField(blank=True, help_text='e.g. smtp.gmail.com', max_length=255, null=True, verbose_name='Servidor SMTP')),
                ('port', models.IntegerField(blank=True, default=587, null=True, verbose_name='Porta SMTP')),
                ('username', models.CharField(blank=True, max_length=255, null=True, verbose_name='Usuário SMTP')),
                ('password', models.CharField(blank=True, max_length=255, null=True, verbose_name='Senha SMTP')),
                ('use_tls', models.BooleanField(default=True, verbose_name='Usar TLS')),
                ('use_ssl', models.BooleanField(default=False, verbose_name='Usar SSL')),
                ('default_from_email', models.EmailField(help_text='e.g. no-reply@seusite.com', max_length=254, verbose_name='E-mail Padrão (From)')),
                ('is_active', models.BooleanField(default=False, help_text='Apenas uma configuração pode estar ativa por vez.', verbose_name='Ativo')),
            ],
            options={
                'verbose_name': 'Configuração de E-mail',
                'verbose_name_plural': 'Configurações de E-mail',
            },
        ),
    ]
