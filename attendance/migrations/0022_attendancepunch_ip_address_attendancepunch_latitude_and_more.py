

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0021_alter_attendancerecord_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancepunch',
            name='ip_address',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='IP'),
        ),
        migrations.AddField(
            model_name='attendancepunch',
            name='latitude',
            field=models.FloatField(blank=True, null=True, verbose_name='Latitude'),
        ),
        migrations.AddField(
            model_name='attendancepunch',
            name='location_address',
            field=models.TextField(blank=True, null=True, verbose_name='Endereço Aproximado'),
        ),
        migrations.AddField(
            model_name='attendancepunch',
            name='longitude',
            field=models.FloatField(blank=True, null=True, verbose_name='Longitude'),
        ),
    ]
