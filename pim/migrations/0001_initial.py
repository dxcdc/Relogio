

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('admin_app', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TerminationReason',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Motivo')),
            ],
            options={
                'verbose_name': 'Motivo de Desligamento',
                'verbose_name_plural': 'Motivos de Desligamento',
            },
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='ID do Funcionário')),
                ('first_name', models.CharField(max_length=100, verbose_name='Nome')),
                ('middle_name', models.CharField(blank=True, default='', max_length=100, verbose_name='Nome do Meio')),
                ('last_name', models.CharField(max_length=100, verbose_name='Sobrenome')),
                ('nick_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Apelido')),
                ('birthday', models.DateField(blank=True, null=True, verbose_name='Data de Nascimento')),
                ('gender', models.IntegerField(blank=True, choices=[(1, 'Masculino'), (2, 'Feminino'), (3, 'Outro')], null=True, verbose_name='Gênero')),
                ('marital_status', models.CharField(blank=True, choices=[('Single', 'Solteiro(a)'), ('Married', 'Casado(a)'), ('Other', 'Outro')], max_length=20, null=True, verbose_name='Estado Civil')),
                ('ethnic_race_code', models.CharField(blank=True, max_length=13, null=True, verbose_name='Etnia')),
                ('smoker', models.BooleanField(default=False, verbose_name='Fumante')),
                ('military_service', models.CharField(blank=True, max_length=100, null=True, verbose_name='Serviço Militar')),
                ('ssn_number', models.CharField(blank=True, max_length=100, null=True, verbose_name='CPF / SSN')),
                ('sin_number', models.CharField(blank=True, max_length=100, null=True, verbose_name='SIN')),
                ('other_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='Outro ID')),
                ('driving_license_no', models.CharField(blank=True, max_length=100, null=True, verbose_name='Nº CNH')),
                ('driving_license_expired_date', models.DateField(blank=True, null=True, verbose_name='Vencimento CNH')),
                ('joined_date', models.DateField(blank=True, null=True, verbose_name='Data de Admissão')),
                ('street1', models.CharField(blank=True, max_length=100, null=True, verbose_name='Endereço 1')),
                ('street2', models.CharField(blank=True, max_length=100, null=True, verbose_name='Endereço 2')),
                ('city', models.CharField(blank=True, max_length=100, null=True, verbose_name='Cidade')),
                ('province', models.CharField(blank=True, max_length=100, null=True, verbose_name='Estado')),
                ('country', models.CharField(blank=True, max_length=100, null=True, verbose_name='País')),
                ('zipcode', models.CharField(blank=True, max_length=20, null=True, verbose_name='CEP')),
                ('home_telephone', models.CharField(blank=True, max_length=50, null=True, verbose_name='Telefone Residencial')),
                ('mobile', models.CharField(blank=True, max_length=50, null=True, verbose_name='Celular')),
                ('work_telephone', models.CharField(blank=True, max_length=50, null=True, verbose_name='Telefone Comercial')),
                ('work_email', models.EmailField(blank=True, max_length=50, null=True, verbose_name='Email Corporativo')),
                ('other_email', models.EmailField(blank=True, max_length=50, null=True, verbose_name='Email Alternativo')),
                ('state', models.CharField(choices=[('ACTIVE', 'Ativo'), ('TERMINATED', 'Desligado')], default='ACTIVE', max_length=20, verbose_name='Estado')),
                ('custom1', models.CharField(blank=True, max_length=250, null=True)),
                ('custom2', models.CharField(blank=True, max_length=250, null=True)),
                ('custom3', models.CharField(blank=True, max_length=250, null=True)),
                ('custom4', models.CharField(blank=True, max_length=250, null=True)),
                ('custom5', models.CharField(blank=True, max_length=250, null=True)),
                ('purged_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('emp_status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.employmentstatus', verbose_name='Status de Emprego')),
                ('job_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.jobcategory', verbose_name='Categoria do Cargo')),
                ('job_title', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.jobtitle', verbose_name='Cargo')),
                ('locations', models.ManyToManyField(blank=True, to='admin_app.location', verbose_name='Localizações')),
                ('nationality', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.nationality', verbose_name='Nacionalidade')),
                ('sub_division', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.subunit', verbose_name='Departamento')),
                ('supervisors', models.ManyToManyField(blank=True, related_name='subordinates', to='pim.employee', verbose_name='Supervisores')),
                ('work_shift', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.workshift', verbose_name='Turno')),
            ],
            options={
                'verbose_name': 'Funcionário',
                'verbose_name_plural': 'Funcionários',
                'ordering': ['last_name', 'first_name'],
            },
        ),
        migrations.CreateModel(
            name='EmpEmergencyContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nome')),
                ('relationship', models.CharField(max_length=100, verbose_name='Parentesco')),
                ('home_phone', models.CharField(blank=True, max_length=50, null=True, verbose_name='Telefone Residencial')),
                ('mobile_phone', models.CharField(blank=True, max_length=50, null=True, verbose_name='Celular')),
                ('office_phone', models.CharField(blank=True, max_length=50, null=True, verbose_name='Telefone Comercial')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emergency_contacts', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Contato de Emergência',
                'verbose_name_plural': 'Contatos de Emergência',
            },
        ),
        migrations.CreateModel(
            name='EmpDependent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nome')),
                ('relationship_type', models.CharField(choices=[('child', 'Filho(a)'), ('spouse', 'Cônjuge'), ('other', 'Outro')], max_length=20, verbose_name='Parentesco')),
                ('relationship', models.CharField(blank=True, max_length=100, null=True)),
                ('date_of_birth', models.DateField(blank=True, null=True, verbose_name='Data de Nascimento')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dependents', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Dependente',
                'verbose_name_plural': 'Dependentes',
            },
        ),
        migrations.CreateModel(
            name='EmpContract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contract_start_date', models.DateField(verbose_name='Início do Contrato')),
                ('contract_end_date', models.DateField(blank=True, null=True, verbose_name='Fim do Contrato')),
                ('contract_file', models.FileField(blank=True, null=True, upload_to='contracts/', verbose_name='Arquivo do Contrato')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contracts', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Contrato',
                'verbose_name_plural': 'Contratos',
            },
        ),
        migrations.CreateModel(
            name='EmployeeAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=200, null=True, verbose_name='Descrição')),
                ('filename', models.CharField(max_length=200, verbose_name='Nome do Arquivo')),
                ('file', models.FileField(upload_to='employee_attachments/', verbose_name='Arquivo')),
                ('file_type', models.CharField(blank=True, max_length=50, null=True)),
                ('file_size', models.IntegerField(blank=True, null=True)),
                ('attached_at', models.DateTimeField(auto_now_add=True)),
                ('attached_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Anexo',
                'verbose_name_plural': 'Anexos',
            },
        ),
        migrations.CreateModel(
            name='EmployeeEducation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('institute', models.CharField(blank=True, max_length=200, null=True, verbose_name='Instituição')),
                ('major', models.CharField(blank=True, max_length=200, null=True, verbose_name='Especialização')),
                ('year', models.IntegerField(blank=True, null=True, verbose_name='Ano')),
                ('gpa', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='GPA/Nota')),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='Início')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='Término')),
                ('education', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.education', verbose_name='Nível de Educação')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='educations', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Formação Educacional',
                'verbose_name_plural': 'Formações Educacionais',
            },
        ),
        migrations.CreateModel(
            name='EmployeeImmigrationRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(choices=[('passport', 'Passaporte'), ('visa', 'Visto')], max_length=20, verbose_name='Tipo de Documento')),
                ('number', models.CharField(max_length=100, verbose_name='Número')),
                ('issue_date', models.DateField(blank=True, null=True, verbose_name='Data de Emissão')),
                ('expiry_date', models.DateField(blank=True, null=True, verbose_name='Data de Validade')),
                ('issued_by', models.CharField(blank=True, max_length=100, null=True, verbose_name='Emitido Por')),
                ('country', models.CharField(blank=True, max_length=100, null=True, verbose_name='País')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='immigration_records', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Documento de Imigração',
                'verbose_name_plural': 'Documentos de Imigração',
            },
        ),
        migrations.CreateModel(
            name='EmployeeLicense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('license_no', models.CharField(blank=True, max_length=100, null=True, verbose_name='Número da Licença')),
                ('issued_date', models.DateField(blank=True, null=True, verbose_name='Data de Emissão')),
                ('expiry_date', models.DateField(blank=True, null=True, verbose_name='Data de Validade')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='licenses', to='pim.employee')),
                ('license', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_app.license', verbose_name='Licença')),
            ],
            options={
                'verbose_name': 'Licença',
                'verbose_name_plural': 'Licenças',
            },
        ),
        migrations.CreateModel(
            name='EmployeeMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscription_paid_by', models.CharField(blank=True, choices=[('individual', 'Individual'), ('employer', 'Empregador'), ('employer_individual', 'Empregador e Individual')], max_length=30, null=True, verbose_name='Pago por')),
                ('subscription_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Taxa')),
                ('subscription_commence_date', models.DateField(blank=True, null=True, verbose_name='Início')),
                ('subscription_renewal_date', models.DateField(blank=True, null=True, verbose_name='Renovação')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='pim.employee')),
                ('membership', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_app.membership', verbose_name='Filiação')),
                ('subscription_currency', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.currencytype', verbose_name='Moeda')),
            ],
            options={
                'verbose_name': 'Filiação',
                'verbose_name_plural': 'Filiações',
            },
        ),
        migrations.CreateModel(
            name='EmployeeSalary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('salary_component', models.CharField(max_length=100, verbose_name='Componente Salarial')),
                ('payment_frequency', models.CharField(blank=True, max_length=50, null=True, verbose_name='Frequência de Pagamento')),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Valor')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('currency', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.currencytype', verbose_name='Moeda')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salaries', to='pim.employee')),
                ('pay_grade', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_app.paygrade', verbose_name='Faixa Salarial')),
            ],
            options={
                'verbose_name': 'Salário',
                'verbose_name_plural': 'Salários',
            },
        ),
        migrations.CreateModel(
            name='EmployeeTerminationRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Data do Desligamento')),
                ('note', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='termination_records', to='pim.employee')),
                ('termination_reason', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='pim.terminationreason', verbose_name='Motivo')),
            ],
            options={
                'verbose_name': 'Registro de Desligamento',
                'verbose_name_plural': 'Registros de Desligamento',
            },
        ),
        migrations.AddField(
            model_name='employee',
            name='termination_record',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='terminated_employee', to='pim.employeeterminationrecord'),
        ),
        migrations.CreateModel(
            name='EmpPicture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('picture', models.ImageField(upload_to='employee_pictures/', verbose_name='Foto')),
                ('file_name', models.CharField(max_length=100)),
                ('file_type', models.CharField(max_length=50)),
                ('employee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='picture', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Foto do Funcionário',
            },
        ),
        migrations.CreateModel(
            name='EmpUsTaxExemption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('federal_status', models.CharField(blank=True, max_length=50, null=True)),
                ('federal_exemptions', models.IntegerField(blank=True, null=True)),
                ('state', models.CharField(blank=True, max_length=100, null=True)),
                ('state_status', models.CharField(blank=True, max_length=50, null=True)),
                ('state_exemptions', models.IntegerField(blank=True, null=True)),
                ('employee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='tax_exemption', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Isenção Fiscal',
            },
        ),
        migrations.CreateModel(
            name='EmpWorkExperience',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employer', models.CharField(max_length=200, verbose_name='Empregador')),
                ('job_title', models.CharField(max_length=200, verbose_name='Cargo')),
                ('from_date', models.DateField(blank=True, null=True, verbose_name='Data de Início')),
                ('to_date', models.DateField(blank=True, null=True, verbose_name='Data de Término')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_experiences', to='pim.employee')),
            ],
            options={
                'verbose_name': 'Experiência Profissional',
                'verbose_name_plural': 'Experiências Profissionais',
            },
        ),
        migrations.CreateModel(
            name='EmployeeLanguage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fluency', models.CharField(blank=True, choices=[('poor', 'Fraco'), ('basic', 'Básico'), ('good', 'Bom'), ('mother_tongue', 'Língua Materna')], max_length=30, null=True, verbose_name='Fluência')),
                ('competency', models.CharField(blank=True, choices=[('reading', 'Leitura'), ('writing', 'Escrita'), ('speaking', 'Fala')], max_length=30, null=True, verbose_name='Competência')),
                ('comment', models.TextField(blank=True, null=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='languages', to='pim.employee')),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_app.language', verbose_name='Idioma')),
            ],
            options={
                'verbose_name': 'Idioma',
                'verbose_name_plural': 'Idiomas',
                'unique_together': {('employee', 'language')},
            },
        ),
        migrations.CreateModel(
            name='EmployeeSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proficiency', models.CharField(blank=True, choices=[('poor', 'Fraco'), ('basic', 'Básico'), ('good', 'Bom'), ('excellent', 'Excelente')], max_length=20, null=True, verbose_name='Proficiência')),
                ('years_of_exp', models.IntegerField(blank=True, null=True, verbose_name='Anos de Experiência')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skills', to='pim.employee')),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_app.skill', verbose_name='Habilidade')),
            ],
            options={
                'verbose_name': 'Habilidade',
                'verbose_name_plural': 'Habilidades',
                'unique_together': {('employee', 'skill')},
            },
        ),
    ]
