

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0022_attendancepunch_ip_address_attendancepunch_latitude_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='timesheetperiod',
            name='accumulated_balance_minutes',
            field=models.IntegerField(default=0, verbose_name='Saldo Acumulado (Minutos)'),
        ),
        migrations.AddField(
            model_name='timesheetperiod',
            name='is_hour_bank_zeroed',
            field=models.BooleanField(default=False, verbose_name='Banco Zerado Neste Mês'),
        ),
    ]
