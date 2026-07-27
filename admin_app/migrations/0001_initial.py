

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='País')),
                ('code', models.CharField(max_length=3, unique=True, verbose_name='Código')),
            ],
            options={
                'verbose_name': 'País',
                'verbose_name_plural': 'Países',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CurrencyType',
            fields=[
                ('id', models.CharField(max_length=10, primary_key=True, serialize=False, verbose_name='Código')),
                ('name', models.CharField(max_length=70, verbose_name='Moeda')),
            ],
            options={
                'verbose_name': 'Moeda',
                'verbose_name_plural': 'Moedas',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Education',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Nível de Educação')),
            ],
            options={
                'verbose_name': 'Nível de Educação',
                'verbose_name_plural': 'Níveis de Educação',
            },
        ),
        migrations.CreateModel(
            name='EmailNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Notificação')),
                ('description', models.TextField(blank=True, null=True)),
                ('is_enabled', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Notificação de Email',
                'verbose_name_plural': 'Notificações de Email',
            },
        ),
        migrations.CreateModel(
            name='EmploymentStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Status')),
            ],
            options={
                'verbose_name': 'Status de Emprego',
                'verbose_name_plural': 'Status de Emprego',
            },
        ),
        migrations.CreateModel(
            name='JobCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Categoria')),
            ],
            options={
                'verbose_name': 'Categoria de Cargo',
                'verbose_name_plural': 'Categorias de Cargo',
            },
        ),
        migrations.CreateModel(
            name='JobTitle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, unique=True, verbose_name='Cargo')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descrição')),
                ('note', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('is_deleted', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Cargo',
                'verbose_name_plural': 'Cargos',
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True, verbose_name='Idioma')),
            ],
            options={
                'verbose_name': 'Idioma',
                'verbose_name_plural': 'Idiomas',
            },
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Licença')),
            ],
            options={
                'verbose_name': 'Licença',
                'verbose_name_plural': 'Licenças',
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nome')),
                ('country', models.CharField(blank=True, max_length=100, null=True, verbose_name='País')),
                ('province', models.CharField(blank=True, max_length=100, null=True, verbose_name='Estado')),
                ('city', models.CharField(blank=True, max_length=100, null=True, verbose_name='Cidade')),
                ('address', models.TextField(blank=True, null=True, verbose_name='Endereço')),
                ('zip_code', models.CharField(blank=True, max_length=20, null=True, verbose_name='CEP')),
                ('phone', models.CharField(blank=True, max_length=30, null=True, verbose_name='Telefone')),
                ('fax', models.CharField(blank=True, max_length=30, null=True, verbose_name='Fax')),
                ('note', models.TextField(blank=True, null=True, verbose_name='Observações')),
            ],
            options={
                'verbose_name': 'Localização',
                'verbose_name_plural': 'Localizações',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Filiação')),
            ],
            options={
                'verbose_name': 'Tipo de Filiação',
                'verbose_name_plural': 'Tipos de Filiação',
            },
        ),
        migrations.CreateModel(
            name='Nationality',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Nacionalidade')),
            ],
            options={
                'verbose_name': 'Nacionalidade',
                'verbose_name_plural': 'Nacionalidades',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nome da Empresa')),
                ('tax_id', models.CharField(blank=True, max_length=30, null=True, verbose_name='CNPJ/Tax ID')),
                ('registration_number', models.CharField(blank=True, max_length=30, null=True, verbose_name='Nº de Registro')),
                ('phone', models.CharField(blank=True, max_length=30, null=True, verbose_name='Telefone')),
                ('fax', models.CharField(blank=True, max_length=30, null=True, verbose_name='Fax')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email')),
                ('country', models.CharField(blank=True, max_length=100, null=True, verbose_name='País')),
                ('province', models.CharField(blank=True, max_length=100, null=True, verbose_name='Estado')),
                ('city', models.CharField(blank=True, max_length=100, null=True, verbose_name='Cidade')),
                ('zip_code', models.CharField(blank=True, max_length=20, null=True, verbose_name='CEP')),
                ('street1', models.CharField(blank=True, max_length=100, null=True, verbose_name='Endereço')),
                ('street2', models.CharField(blank=True, max_length=100, null=True)),
                ('note', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('logo', models.ImageField(blank=True, null=True, upload_to='organization/', verbose_name='Logo')),
            ],
            options={
                'verbose_name': 'Organização',
            },
        ),
        migrations.CreateModel(
            name='PayGrade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Faixa Salarial')),
            ],
            options={
                'verbose_name': 'Faixa Salarial',
                'verbose_name_plural': 'Faixas Salariais',
            },
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True, verbose_name='Habilidade')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Habilidade',
                'verbose_name_plural': 'Habilidades',
            },
        ),
        migrations.CreateModel(
            name='WorkShift',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Nome do Turno')),
                ('hours_per_day', models.DecimalField(decimal_places=2, default=8, max_digits=4, verbose_name='Horas por Dia')),
                ('start_time', models.TimeField(verbose_name='Hora de Início')),
                ('end_time', models.TimeField(verbose_name='Hora de Término')),
            ],
            options={
                'verbose_name': 'Turno',
                'verbose_name_plural': 'Turnos',
            },
        ),
        migrations.CreateModel(
            name='Province',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Estado')),
                ('code', models.CharField(max_length=10, verbose_name='Código')),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='provinces', to='admin_app.country')),
            ],
            options={
                'verbose_name': 'Estado',
                'verbose_name_plural': 'Estados',
            },
        ),
        migrations.CreateModel(
            name='Subunit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nome')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descrição')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='admin_app.subunit', verbose_name='Unidade Pai')),
            ],
            options={
                'verbose_name': 'Unidade Organizacional',
                'verbose_name_plural': 'Unidades Organizacionais',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PayGradeCurrency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_salary', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name='Salário Mínimo')),
                ('max_salary', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name='Salário Máximo')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_app.currencytype')),
                ('pay_grade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='currencies', to='admin_app.paygrade')),
            ],
            options={
                'verbose_name': 'Faixa Salarial por Moeda',
                'unique_together': {('pay_grade', 'currency')},
            },
        ),
    ]
