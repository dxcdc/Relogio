

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0024_rename_total_extra_50_minutes_timesheetperiod_total_extra_60_minutes_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendanceclosingsettings',
            name='hour_bank_closing_months',
        ),
        migrations.AddField(
            model_name='attendanceclosingsettings',
            name='hour_bank_reset_months',
            field=models.CharField(default='4,10', max_length=50, verbose_name='Meses de Zeramento (ex: 4,10)'),
        ),
        migrations.AddField(
            model_name='attendanceclosingsettings',
            name='overtime_multiplier_weekday',
            field=models.FloatField(default=1.6, verbose_name='Multiplicador HE Semanal'),
        ),
        migrations.AddField(
            model_name='attendanceclosingsettings',
            name='overtime_multiplier_weekend',
            field=models.FloatField(default=2.0, verbose_name='Multiplicador HE DSR/Feriado'),
        ),
    ]
