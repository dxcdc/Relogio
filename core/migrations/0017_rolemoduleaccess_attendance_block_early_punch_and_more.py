

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_rolemoduleaccess_attendance_photo_all_punches'),
    ]

    operations = [
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='attendance_block_early_punch',
            field=models.BooleanField(default=False, verbose_name='Bloquear ponto antecipado'),
        ),
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='attendance_block_off_days',
            field=models.BooleanField(default=False, verbose_name='Bloquear ponto em dias de folga'),
        ),
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='netgram_post',
            field=models.BooleanField(default=True, verbose_name='Permitir Postagens no Netgram'),
        ),
    ]
