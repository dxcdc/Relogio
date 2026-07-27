

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AttendanceRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('punch_in_utc_time', models.DateTimeField(blank=True, null=True, verbose_name='Entrada (UTC)')),
                ('punch_in_note', models.TextField(blank=True, null=True, verbose_name='Observação de Entrada')),
                ('punch_in_time_offset', models.CharField(blank=True, max_length=10, null=True)),
                ('punch_in_user_time', models.DateTimeField(blank=True, null=True, verbose_name='Entrada (Local)')),
                ('punch_out_utc_time', models.DateTimeField(blank=True, null=True, verbose_name='Saída (UTC)')),
                ('punch_out_note', models.TextField(blank=True, null=True, verbose_name='Observação de Saída')),
                ('punch_out_time_offset', models.CharField(blank=True, max_length=10, null=True)),
                ('punch_out_user_time', models.DateTimeField(blank=True, null=True, verbose_name='Saída (Local)')),
                ('state', models.CharField(choices=[('PUNCHED IN', 'Entrada Registrada'), ('PUNCHED OUT', 'Saída Registrada')], default='PUNCHED IN', max_length=20, verbose_name='Estado')),
            ],
            options={
                'verbose_name': 'Registro de Ponto',
                'verbose_name_plural': 'Registros de Ponto',
                'ordering': ['-punch_in_utc_time'],
            },
        ),
    ]
