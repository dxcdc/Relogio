

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0016_attendancerecord_punch_in_photo_and_more'),
        ('pim', '0004_orghierarchyrequest'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PendingPunchRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('PUNCH_IN', 'Entrada'), ('PUNCH_OUT', 'Saída Final')], max_length=10, verbose_name='Tipo')),
                ('requested_at', models.DateTimeField(verbose_name='Horário da Tentativa')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='attendance_photos/', verbose_name='Foto Capturada')),
                ('lat', models.FloatField(blank=True, null=True, verbose_name='Latitude')),
                ('lng', models.FloatField(blank=True, null=True, verbose_name='Longitude')),
                ('fail_reason', models.TextField(verbose_name='Motivo da Pendência')),
                ('status', models.CharField(choices=[('PENDING', 'Aguardando Aprovação'), ('APPROVED', 'Aprovado'), ('REJECTED', 'Rejeitado')], default='PENDING', max_length=10, verbose_name='Status')),
                ('reviewed_at', models.DateTimeField(blank=True, null=True, verbose_name='Revisado em')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pending_punches', to='pim.employee', verbose_name='Funcionário')),
                ('linked_record', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='attendance.attendancerecord', verbose_name='Registro Vinculado')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Revisado por')),
            ],
            options={
                'verbose_name': 'Batida Pendente de Aprovação',
                'verbose_name_plural': 'Batidas Pendentes de Aprovação',
                'ordering': ['-requested_at'],
            },
        ),
    ]
