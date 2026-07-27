

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0019_remove_attendanceclosingsettings_company_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendanceclosingsettings',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Regra Ativa'),
        ),
    ]
