

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0004_feature_action_log_rejection_auditlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='leavetype',
            name='default_days',
            field=models.PositiveIntegerField(blank=True, help_text='Quantos dias consecutivos o sistema deve calcular automaticamente. Ex: 3 (para Casamento).', null=True, verbose_name='Dias Automáticos'),
        ),
    ]
