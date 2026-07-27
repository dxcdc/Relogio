

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buzz', '0003_alter_buzzcomment_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BugReportScreenshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='bug_screenshots/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('bug_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='screenshots', to='buzz.bugreport')),
            ],
            options={
                'verbose_name': 'Screenshot de Bug',
                'verbose_name_plural': 'Screenshots de Bug',
                'ordering': ['uploaded_at'],
            },
        ),
    ]
