

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0002_legalentity'),
        ('pim', '0002_employee_work_schedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='legal_entity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.legalentity', verbose_name='Empresa Contratante'),
        ),
    ]
