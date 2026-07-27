

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0003_subunit_supervisor'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='allowed_ipv4',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='IP Público Permitido'),
        ),
        migrations.AddField(
            model_name='location',
            name='latitude',
            field=models.FloatField(blank=True, null=True, verbose_name='Latitude'),
        ),
        migrations.AddField(
            model_name='location',
            name='longitude',
            field=models.FloatField(blank=True, null=True, verbose_name='Longitude'),
        ),
        migrations.AddField(
            model_name='location',
            name='radius_meters',
            field=models.IntegerField(blank=True, null=True, verbose_name='Raio do Ponto (Metros)'),
        ),
    ]
