

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalEntity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Razão Social / Nome Fantasia')),
                ('tax_id', models.CharField(max_length=30, unique=True, verbose_name='CNPJ')),
                ('registration_number', models.CharField(blank=True, max_length=50, null=True, verbose_name='Inscrição Estadual/Municipal')),
                ('phone', models.CharField(blank=True, max_length=30, null=True, verbose_name='Telefone')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email')),
                ('address', models.TextField(blank=True, null=True, verbose_name='Endereço Completo')),
                ('note', models.TextField(blank=True, null=True, verbose_name='Observações')),
            ],
            options={
                'verbose_name': 'Empresa/Filial',
                'verbose_name_plural': 'Empresas/Filiais',
                'ordering': ['name'],
            },
        ),
    ]
