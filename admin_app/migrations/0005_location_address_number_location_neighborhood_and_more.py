

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0004_location_allowed_ipv4_location_latitude_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='address_number',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Número'),
        ),
        migrations.AddField(
            model_name='location',
            name='neighborhood',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Bairro'),
        ),
        migrations.AlterField(
            model_name='location',
            name='address',
            field=models.TextField(blank=True, null=True, verbose_name='Endereço (Rua/Avenida)'),
        ),
    ]
