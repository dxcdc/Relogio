

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0005_alter_attendanceadjustment_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workschedule',
            name='work_days',
            field=models.CharField(default='0,1,2,3,4', help_text='Dias da semana em que esta escala é ativa (0=Seg, 6=Dom)', max_length=20, verbose_name='Dias de Trabalho'),
        ),
    ]
