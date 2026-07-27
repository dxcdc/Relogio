

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0020_attendanceclosingsettings_is_active'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attendancerecord',
            options={'ordering': ['-date'], 'verbose_name': 'Registro de Ponto Diário', 'verbose_name_plural': 'Registros de Ponto Diários'},
        ),
        migrations.RemoveField(
            model_name='attendanceadjustment',
            name='punch_in',
        ),
        migrations.RemoveField(
            model_name='attendanceadjustment',
            name='punch_lunch_in',
        ),
        migrations.RemoveField(
            model_name='attendanceadjustment',
            name='punch_lunch_out',
        ),
        migrations.RemoveField(
            model_name='attendanceadjustment',
            name='punch_out',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='fraud_reason',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='is_flagged_location',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_in_note',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_in_photo',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_in_user_time',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_in_utc_time',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_lunch_in_note',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_lunch_in_user_time',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_lunch_in_utc_time',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_lunch_out_note',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_lunch_out_user_time',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_lunch_out_utc_time',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_out_note',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_out_photo',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_out_user_time',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='punch_out_utc_time',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='state',
        ),
        migrations.AddField(
            model_name='attendanceadjustment',
            name='requested_punches',
            field=models.JSONField(default=list, verbose_name='Horários Solicitados'),
        ),
        migrations.AlterField(
            model_name='pendingpunchrequest',
            name='action_type',
            field=models.CharField(choices=[('IN', 'Entrada (Iniciar)'), ('OUT', 'Saída (Pausar)')], max_length=20, verbose_name='Tipo'),
        ),
        migrations.CreateModel(
            name='AttendancePunch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('punch_type', models.CharField(choices=[('IN', 'Entrada/Retorno (Iniciar)'), ('OUT', 'Saída/Pausa (Pausar)')], max_length=10, verbose_name='Ação')),
                ('timestamp_utc', models.DateTimeField(verbose_name='Horário (UTC)')),
                ('timestamp_user', models.DateTimeField(verbose_name='Horário (Local)')),
                ('note', models.TextField(blank=True, null=True, verbose_name='Observação')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='attendance_photos/', verbose_name='Foto Capturada')),
                ('is_flagged_location', models.BooleanField(default=False, verbose_name='Fora do Local Autorizado')),
                ('fraud_reason', models.TextField(blank=True, null=True, verbose_name='Detalhes de Fraude')),
                ('attendance_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='punches', to='attendance.attendancerecord')),
            ],
            options={
                'verbose_name': 'Batida de Ponto',
                'verbose_name_plural': 'Batidas de Ponto',
                'ordering': ['timestamp_utc'],
            },
        ),
    ]
