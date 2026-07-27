

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_announcement_expires_at_announcementcomment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='buzz_post_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='ID do Post no Netgram'),
        ),
    ]
