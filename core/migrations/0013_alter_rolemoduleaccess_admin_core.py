

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_rolemoduleaccess_admin_attendance_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rolemoduleaccess',
            name='admin_core',
            field=models.BooleanField(default=True, verbose_name='Admin: Cadastros Base'),
        ),
    ]
