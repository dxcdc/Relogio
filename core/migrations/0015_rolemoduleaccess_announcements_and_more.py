

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_orangeuser_fcm_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='announcements',
            field=models.BooleanField(default=True, verbose_name='Mural de Avisos'),
        ),
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='reports',
            field=models.BooleanField(default=True, verbose_name='Relatórios Gerenciais'),
        ),
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='support_tickets',
            field=models.BooleanField(default=True, verbose_name='Suporte & Chamados'),
        ),
    ]
