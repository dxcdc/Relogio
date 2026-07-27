

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ClaimAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='claim_attachments/', verbose_name='Arquivo')),
                ('file_name', models.CharField(max_length=200)),
                ('description', models.CharField(blank=True, max_length=200, null=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Anexo',
                'verbose_name_plural': 'Anexos',
            },
        ),
        migrations.CreateModel(
            name='ClaimEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Nome do Evento')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descrição')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
            ],
            options={
                'verbose_name': 'Evento de Reembolso',
                'verbose_name_plural': 'Eventos de Reembolso',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ClaimExpense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expense_date', models.DateField(verbose_name='Data')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Valor')),
                ('note', models.TextField(blank=True, null=True, verbose_name='Observações')),
            ],
            options={
                'verbose_name': 'Despesa',
                'verbose_name_plural': 'Despesas',
                'ordering': ['expense_date'],
            },
        ),
        migrations.CreateModel(
            name='ClaimRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference_id', models.CharField(blank=True, max_length=50, null=True, verbose_name='Referência')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descrição')),
                ('status', models.CharField(choices=[('INITIATED', 'Iniciada'), ('SUBMITTED', 'Enviada'), ('APPROVED', 'Aprovada'), ('REJECTED', 'Rejeitada'), ('CANCELLED', 'Cancelada'), ('PAID', 'Paga')], default='INITIATED', max_length=20, verbose_name='Status')),
                ('submitted_date', models.DateField(blank=True, null=True, verbose_name='Data de Envio')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Solicitação de Reembolso',
                'verbose_name_plural': 'Solicitações de Reembolso',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ExpenseType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Tipo de Despesa')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descrição')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
            ],
            options={
                'verbose_name': 'Tipo de Despesa',
                'verbose_name_plural': 'Tipos de Despesa',
                'ordering': ['name'],
            },
        ),
    ]
