

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0015_workschedule_automatic_break_minutes'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancerecord',
            name='punch_in_photo',
            field=models.ImageField(blank=True, null=True, upload_to='attendance_photos/', verbose_name='Foto (Entrada)'),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='punch_out_photo',
            field=models.ImageField(blank=True, null=True, upload_to='attendance_photos/', verbose_name='Foto (Saída)'),
        ),
    ]
