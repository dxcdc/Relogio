

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0004_attendanceadjustment'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attendanceadjustment',
            options={'ordering': ['-created_at'], 'verbose_name': 'Solicitação de Ajuste', 'verbose_name_plural': 'Solicitações de Ajuste'},
        ),
        migrations.AlterModelOptions(
            name='attendancerecord',
            options={'ordering': ['-date', '-punch_in_utc_time'], 'verbose_name': 'Registro de Ponto', 'verbose_name_plural': 'Registros de Ponto'},
        ),
        migrations.RemoveField(
            model_name='attendanceadjustment',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_in_time_offset',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_out_time_offset',
        ),
        migrations.AddField(
            model_name='attendanceadjustment',
            name='punch_lunch_in',
            field=models.TimeField(blank=True, null=True, verbose_name='Retorno do Almoço Solicitado'),
        ),
        migrations.AddField(
            model_name='attendanceadjustment',
            name='punch_lunch_out',
            field=models.TimeField(blank=True, null=True, verbose_name='Saída para Almoço Solicitada'),
        ),
        migrations.AddField(
            model_name='attendanceadjustment',
            name='review_note',
            field=models.TextField(blank=True, null=True, verbose_name='Nota de Revisão'),
        ),
        migrations.AddField(
            model_name='attendanceadjustment',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Data do Ponto'),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='punch_lunch_in_note',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='punch_lunch_in_user_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Retorno Almoço (Local)'),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='punch_lunch_in_utc_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Retorno Almoço (UTC)'),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='punch_lunch_out_note',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='punch_lunch_out_user_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Saída Almoço (Local)'),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='punch_lunch_out_utc_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Saída Almoço (UTC)'),
        ),
        migrations.AlterField(
            model_name='attendanceadjustment',
            name='attendance_record',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='adjustments', to='attendance.attendancerecord'),
        ),
        migrations.AlterField(
            model_name='attendanceadjustment',
            name='punch_out',
            field=models.TimeField(blank=True, null=True, verbose_name='Saída Final Solicitada'),
        ),
        migrations.AlterField(
            model_name='attendanceadjustment',
            name='reviewed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='attendancerecord',
            name='punch_in_note',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='attendancerecord',
            name='punch_out_note',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='attendancerecord',
            name='state',
            field=models.CharField(choices=[('PUNCHED_IN', 'Entrada Registrada'), ('LUNCH_OUT', 'Saída para Almoço'), ('LUNCH_IN', 'Retorno do Almoço'), ('PUNCHED_OUT', 'Saída Final')], default='PUNCHED_IN', max_length=20, verbose_name='Estado'),
        ),
    ]
