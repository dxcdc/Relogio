

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0014_attendancerecord_fraud_reason_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workschedule',
            name='automatic_break_minutes',
            field=models.PositiveIntegerField(default=0, help_text='Tempo deduzido automaticamente caso o funcionário não registre a saída/retorno do intervalo.', verbose_name='Intervalo Automático (min)'),
        ),
    ]
