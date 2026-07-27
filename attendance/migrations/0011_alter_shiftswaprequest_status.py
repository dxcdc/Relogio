

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0010_shiftswaprequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shiftswaprequest',
            name='status',
            field=models.CharField(choices=[('PENDING_TARGET', 'Aguardando Colega'), ('PENDING_SUPERVISOR', 'Aguardando Supervisor'), ('PENDING_HR', 'Aguardando RH'), ('APPROVED', 'Aprovado'), ('REJECTED', 'Rejeitado')], default='PENDING_TARGET', max_length=30, verbose_name='Status'),
        ),
    ]
