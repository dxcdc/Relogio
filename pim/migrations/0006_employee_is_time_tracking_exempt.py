

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pim', '0005_alter_employee_city'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='is_time_tracking_exempt',
            field=models.BooleanField(default=False, verbose_name='Isento de Ponto (Cargo de Confiança/Sócio)'),
        ),
    ]
