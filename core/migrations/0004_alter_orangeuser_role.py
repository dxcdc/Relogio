

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orangeuser',
            name='role',
            field=models.CharField(choices=[('Admin', 'Administrador'), ('HR', 'Recursos Humanos (RH)'), ('ESS', 'Funcionário (ESS)'), ('Supervisor', 'Supervisor')], default='ESS', max_length=20),
        ),
    ]
