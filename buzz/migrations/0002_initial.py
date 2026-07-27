

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('buzz', '0001_initial'),
        ('pim', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='buzzcomment',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pim.employee'),
        ),
        migrations.AddField(
            model_name='buzzlikeoncomment',
            name='comment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='buzz.buzzcomment'),
        ),
        migrations.AddField(
            model_name='buzzlikeoncomment',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pim.employee'),
        ),
        migrations.AddField(
            model_name='buzzlikeonshare',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pim.employee'),
        ),
        migrations.AddField(
            model_name='buzzpost',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buzz_posts', to='pim.employee'),
        ),
        migrations.AddField(
            model_name='buzzphoto',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='buzz.buzzpost'),
        ),
        migrations.AddField(
            model_name='buzzlink',
            name='post',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='link', to='buzz.buzzpost'),
        ),
        migrations.AddField(
            model_name='buzzshare',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buzz_shares', to='pim.employee'),
        ),
        migrations.AddField(
            model_name='buzzshare',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shares', to='buzz.buzzpost'),
        ),
        migrations.AddField(
            model_name='buzzlikeonshare',
            name='share',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='buzz.buzzshare'),
        ),
        migrations.AddField(
            model_name='buzzcomment',
            name='share',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='buzz.buzzshare'),
        ),
        migrations.AlterUniqueTogether(
            name='buzzlikeoncomment',
            unique_together={('comment', 'employee')},
        ),
        migrations.AlterUniqueTogether(
            name='buzzlikeonshare',
            unique_together={('share', 'employee')},
        ),
    ]
