

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_alter_rolemoduleaccess_admin_core'),
    ]

    operations = [
        migrations.AddField(
            model_name='orangeuser',
            name='fcm_token',
            field=models.CharField(blank=True, help_text='Token do dispositivo móvel para envio de push notifications via Firebase.', max_length=500, null=True, verbose_name='Token FCM (Push Notification)'),
        ),
    ]
