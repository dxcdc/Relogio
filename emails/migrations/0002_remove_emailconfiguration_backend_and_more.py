

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emails', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emailconfiguration',
            name='backend',
        ),
        migrations.AddField(
            model_name='emailconfiguration',
            name='api_key',
            field=models.CharField(blank=True, help_text='Chave da API para Resend, Sendgrid, etc.', max_length=255, null=True, verbose_name='Token de Acesso / API Key'),
        ),
        migrations.AddField(
            model_name='emailconfiguration',
            name='backend_type',
            field=models.CharField(choices=[('smtp', 'SMTP Tradicional'), ('resend', 'Resend API (Anymail)'), ('sendgrid', 'SendGrid API (Anymail)')], default='smtp', max_length=50, verbose_name='Tipo de Servidor'),
        ),
        migrations.AlterField(
            model_name='emailconfiguration',
            name='use_ssl',
            field=models.BooleanField(default=False, verbose_name='Usar SSL (SMTP)'),
        ),
        migrations.AlterField(
            model_name='emailconfiguration',
            name='use_tls',
            field=models.BooleanField(default=True, verbose_name='Usar TLS (SMTP)'),
        ),
    ]
