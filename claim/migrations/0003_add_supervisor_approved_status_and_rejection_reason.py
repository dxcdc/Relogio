

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('claim', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='claimrequest',
            name='rejection_reason',
            field=models.TextField(blank=True, null=True, verbose_name='Motivo da Rejeição'),
        ),
        migrations.AlterField(
            model_name='claimrequest',
            name='status',
            field=models.CharField(choices=[('INITIATED', 'Iniciada'), ('SUBMITTED', 'Enviada'), ('SUPERVISOR_APPROVED', 'Ag. RH/Admin'), ('APPROVED', 'Aprovada'), ('REJECTED', 'Rejeitada'), ('CANCELLED', 'Cancelada'), ('PAID', 'Paga')], default='INITIATED', max_length=20, verbose_name='Status'),
        ),
    ]
