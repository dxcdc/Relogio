

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0002_add_attachment_to_leave_request'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leaverequest',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pendente'), ('SUPERVISOR_APPROVED', 'Ag. aprovação do RH'), ('APPROVED', 'Aprovada'), ('REJECTED', 'Rejeitada'), ('CANCELLED', 'Cancelada'), ('REQUESTED_MORE_INFO', 'Aguardando Informações')], default='PENDING', max_length=30, verbose_name='Status'),
        ),
    ]
