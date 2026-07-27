

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('performance', '0003_survey_target_city_alter_survey_target_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='survey',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Data e Hora Limite'),
        ),
    ]
