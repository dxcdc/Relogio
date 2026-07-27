

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaverequest',
            name='attachment',
            field=models.FileField(blank=True, null=True, upload_to='leave_attachments/', verbose_name='Atestado / Documento'),
        ),
    ]
