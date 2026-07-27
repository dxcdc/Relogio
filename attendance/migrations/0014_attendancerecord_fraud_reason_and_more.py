

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0013_alter_attendanceadjustment_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancerecord',
            name='fraud_reason',
            field=models.TextField(blank=True, null=True, verbose_name='Detalhes do Ponto Fora do Local'),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='is_flagged_location',
            field=models.BooleanField(default=False, verbose_name='Ponto Fora do Local Autorizado'),
        ),
    ]
