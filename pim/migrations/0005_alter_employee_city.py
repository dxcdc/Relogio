

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0006_city'),
        ('pim', '0004_orghierarchyrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='city',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.city', verbose_name='Cidade Base'),
        ),
    ]
