

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0006_city'),
        ('leave', '0005_leavetype_default_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='holiday',
            name='cities',
            field=models.ManyToManyField(blank=True, to='admin_app.city', verbose_name='Cidades (Se não for global)'),
        ),
        migrations.AddField(
            model_name='holiday',
            name='is_global',
            field=models.BooleanField(default=True, verbose_name='Feriado Global (Todos os locais)'),
        ),
    ]
