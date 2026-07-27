

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0005_location_address_number_location_neighborhood_and_more'),
        ('attendance', '0018_attendanceclosingsettings_dailytimebalance_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendanceclosingsettings',
            name='company_name',
        ),
        migrations.AddField(
            model_name='attendanceclosingsettings',
            name='legal_entity',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attendance_settings', to='admin_app.legalentity', verbose_name='Empresa / Filial (Vazio = Global)'),
        ),
        migrations.AlterField(
            model_name='pendingpunchrequest',
            name='action_type',
            field=models.CharField(choices=[('PUNCH_IN', 'Entrada'), ('PUNCH_LU_OUT', 'Saída Almoço'), ('PUNCH_LU_IN', 'Volta Almoço'), ('PUNCH_OUT', 'Saída Final')], max_length=20, verbose_name='Tipo'),
        ),
    ]
