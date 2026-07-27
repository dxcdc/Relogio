

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0006_city'),
        ('performance', '0002_survey_surveyquestion_surveyresponse_surveyanswer'),
    ]

    operations = [
        migrations.AddField(
            model_name='survey',
            name='target_city',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.city'),
        ),
        migrations.AlterField(
            model_name='survey',
            name='target_type',
            field=models.CharField(choices=[('ALL', 'Todos os Funcionários'), ('LEGAL_ENTITY', 'Empresa / CNPJ'), ('SUBUNIT', 'Departamento Específico'), ('CITY', 'Filial Específica (Cidade)')], default='ALL', max_length=20, verbose_name='Público Alvo'),
        ),
    ]
