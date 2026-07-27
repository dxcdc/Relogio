

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0023_timesheetperiod_accumulated_balance_minutes_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='timesheetperiod',
            old_name='total_extra_50_minutes',
            new_name='total_extra_60_minutes',
        ),
        migrations.RemoveField(
            model_name='dailytimebalance',
            name='extra_50_minutes',
        ),
        migrations.AddField(
            model_name='dailytimebalance',
            name='extra_60_minutes',
            field=models.IntegerField(default=0, verbose_name='HE 60%'),
        ),
    ]
