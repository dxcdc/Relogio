

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_rolemoduleaccess_announcements_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rolemoduleaccess',
            name='attendance_photo_all_punches',
            field=models.BooleanField(default=False, verbose_name='Exigir foto em todas as batidas'),
        ),
    ]
