

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0002_legalentity'),
        ('pim', '0004_orghierarchyrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='subunit',
            name='supervisor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_subunits', to='pim.employee', verbose_name='Supervisor do Departamento'),
        ),
    ]
