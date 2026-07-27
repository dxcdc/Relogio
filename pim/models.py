from django.db import models


class Employee(models.Model):
    """Funcionário - modelo principal do PIM"""
    GENDER_MALE = 1
    GENDER_FEMALE = 2
    GENDER_OTHER = 3
    GENDER_CHOICES = [
        (GENDER_MALE, 'Masculino'),
        (GENDER_FEMALE, 'Feminino'),
        (GENDER_OTHER, 'Outro'),
    ]

    MARITAL_SINGLE = 'Single'
    MARITAL_MARRIED = 'Married'
    MARITAL_OTHER = 'Other'
    MARITAL_CHOICES = [
        (MARITAL_SINGLE, 'Solteiro(a)'),
        (MARITAL_MARRIED, 'Casado(a)'),
        (MARITAL_OTHER, 'Outro'),
    ]

    STATE_ACTIVE = 'ACTIVE'
    STATE_TERMINATED = 'TERMINATED'
    STATE_CHOICES = [
        (STATE_ACTIVE, 'Ativo'),
        (STATE_TERMINATED, 'Desligado'),
    ]

    
    employee_id = models.CharField(max_length=50, blank=True, null=True, unique=True, verbose_name='ID do Funcionário')
    first_name = models.CharField(max_length=100, verbose_name='Nome')
    middle_name = models.CharField(max_length=100, blank=True, default='', verbose_name='Nome do Meio')
    last_name = models.CharField(max_length=100, verbose_name='Sobrenome')
    nick_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Apelido')

    birthday = models.DateField(null=True, blank=True, verbose_name='Data de Nascimento')
    gender = models.IntegerField(choices=GENDER_CHOICES, null=True, blank=True, verbose_name='Gênero')
    marital_status = models.CharField(max_length=20, choices=MARITAL_CHOICES, null=True, blank=True, verbose_name='Estado Civil')
    nationality = models.ForeignKey(
        'admin_app.Nationality', null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name='Nacionalidade'
    )
    ethnic_race_code = models.CharField(max_length=13, null=True, blank=True, verbose_name='Etnia')
    smoker = models.BooleanField(default=False, verbose_name='Fumante')
    military_service = models.CharField(max_length=100, blank=True, null=True, verbose_name='Serviço Militar')

    
    ssn_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='CPF / SSN')
    sin_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='SIN')
    other_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='Outro ID')
    driving_license_no = models.CharField(max_length=100, blank=True, null=True, verbose_name='Nº CNH')
    driving_license_expired_date = models.DateField(null=True, blank=True, verbose_name='Vencimento CNH')

    
    job_title = models.ForeignKey(
        'admin_app.JobTitle', null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name='Cargo'
    )
    job_category = models.ForeignKey(
        'admin_app.JobCategory', null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name='Categoria do Cargo'
    )
    emp_status = models.ForeignKey(
        'admin_app.EmploymentStatus', null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name='Status de Emprego'
    )
    sub_division = models.ForeignKey(
        'admin_app.Subunit', null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name='Departamento'
    )
    legal_entity = models.ForeignKey(
        'admin_app.LegalEntity', null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name='Empresa Contratante'
    )
    locations = models.ManyToManyField(
        'admin_app.Location', blank=True, verbose_name='Localizações'
    )
    joined_date = models.DateField(null=True, blank=True, verbose_name='Data de Admissão')

    
    street1 = models.CharField(max_length=100, blank=True, null=True, verbose_name='Endereço 1')
    street2 = models.CharField(max_length=100, blank=True, null=True, verbose_name='Endereço 2')
    city = models.ForeignKey('admin_app.City', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Cidade Base')
    province = models.CharField(max_length=100, blank=True, null=True, verbose_name='Estado')
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name='País')
    zipcode = models.CharField(max_length=20, blank=True, null=True, verbose_name='CEP')
    home_telephone = models.CharField(max_length=50, blank=True, null=True, verbose_name='Telefone Residencial')
    mobile = models.CharField(max_length=50, blank=True, null=True, verbose_name='Celular')
    work_telephone = models.CharField(max_length=50, blank=True, null=True, verbose_name='Telefone Comercial')
    work_email = models.EmailField(max_length=50, blank=True, null=True, verbose_name='Email Corporativo')
    other_email = models.EmailField(max_length=50, blank=True, null=True, verbose_name='Email Alternativo')

    
    supervisors = models.ManyToManyField(
        'self', blank=True, symmetrical=False,
        related_name='subordinates', verbose_name='Supervisores'
    )

    
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=STATE_ACTIVE, verbose_name='Estado')
    termination_record = models.OneToOneField(
        'EmployeeTerminationRecord', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='terminated_employee'
    )

    
    work_shift = models.ForeignKey(
        'admin_app.WorkShift', null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name='Turno'
    )
    work_schedule = models.ForeignKey(
        'attendance.WorkSchedule', null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name='Escala de Trabalho',
        related_name='employees'
    )
    is_time_tracking_exempt = models.BooleanField(default=False, verbose_name='Isento de Ponto (Cargo de Confiança/Sócio)')

    
    custom1 = models.CharField(max_length=250, blank=True, null=True)
    custom2 = models.CharField(max_length=250, blank=True, null=True)
    custom3 = models.CharField(max_length=250, blank=True, null=True)
    custom4 = models.CharField(max_length=250, blank=True, null=True)
    custom5 = models.CharField(max_length=250, blank=True, null=True)

    purged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return ' '.join(parts)

    def is_active(self):
        return self.state == self.STATE_ACTIVE


class EmpPicture(models.Model):
    """Foto do funcionário"""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='picture')
    picture = models.ImageField(upload_to='employee_pictures/', verbose_name='Foto')
    file_name = models.CharField(max_length=100)
    file_type = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'Foto do Funcionário'

    def __str__(self):
        return f"Foto de {self.employee}"


class EmpDependent(models.Model):
    """Dependente do funcionário"""
    RELATIONSHIP_CHOICES = [
        ('child', 'Filho(a)'),
        ('spouse', 'Cônjuge'),
        ('other', 'Outro'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='dependents')
    name = models.CharField(max_length=100, verbose_name='Nome')
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, verbose_name='Parentesco')
    relationship = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True, verbose_name='Data de Nascimento')

    class Meta:
        verbose_name = 'Dependente'
        verbose_name_plural = 'Dependentes'

    def __str__(self):
        return f"{self.name} ({self.employee})"


class EmpEmergencyContact(models.Model):
    """Contato de emergência"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100, verbose_name='Nome')
    relationship = models.CharField(max_length=100, verbose_name='Parentesco')
    home_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name='Telefone Residencial')
    mobile_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name='Celular')
    office_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name='Telefone Comercial')

    class Meta:
        verbose_name = 'Contato de Emergência'
        verbose_name_plural = 'Contatos de Emergência'

    def __str__(self):
        return f"{self.name} - {self.employee}"


class EmployeeImmigrationRecord(models.Model):
    """Documentos de imigração/passaporte"""
    TYPE_PASSPORT = 'passport'
    TYPE_VISA = 'visa'
    TYPE_CHOICES = [
        (TYPE_PASSPORT, 'Passaporte'),
        (TYPE_VISA, 'Visto'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='immigration_records')
    document_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='Tipo de Documento')
    number = models.CharField(max_length=100, verbose_name='Número')
    issue_date = models.DateField(null=True, blank=True, verbose_name='Data de Emissão')
    expiry_date = models.DateField(null=True, blank=True, verbose_name='Data de Validade')
    issued_by = models.CharField(max_length=100, blank=True, null=True, verbose_name='Emitido Por')
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name='País')
    comment = models.TextField(blank=True, null=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Documento de Imigração'
        verbose_name_plural = 'Documentos de Imigração'

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.employee}"


class EmpWorkExperience(models.Model):
    """Experiência profissional"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='work_experiences')
    employer = models.CharField(max_length=200, verbose_name='Empregador')
    job_title = models.CharField(max_length=200, verbose_name='Cargo')
    from_date = models.DateField(null=True, blank=True, verbose_name='Data de Início')
    to_date = models.DateField(null=True, blank=True, verbose_name='Data de Término')
    comment = models.TextField(blank=True, null=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Experiência Profissional'
        verbose_name_plural = 'Experiências Profissionais'

    def __str__(self):
        return f"{self.job_title} em {self.employer}"


class EmployeeEducation(models.Model):
    """Formação educacional"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='educations')
    education = models.ForeignKey('admin_app.Education', on_delete=models.SET_NULL, null=True, verbose_name='Nível de Educação')
    institute = models.CharField(max_length=200, blank=True, null=True, verbose_name='Instituição')
    major = models.CharField(max_length=200, blank=True, null=True, verbose_name='Especialização')
    year = models.IntegerField(null=True, blank=True, verbose_name='Ano')
    gpa = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='GPA/Nota')
    start_date = models.DateField(null=True, blank=True, verbose_name='Início')
    end_date = models.DateField(null=True, blank=True, verbose_name='Término')

    class Meta:
        verbose_name = 'Formação Educacional'
        verbose_name_plural = 'Formações Educacionais'

    def __str__(self):
        return f"{self.education} - {self.employee}"


class EmployeeSkill(models.Model):
    """Habilidades do funcionário"""
    PROFICIENCY_CHOICES = [
        ('poor', 'Fraco'),
        ('basic', 'Básico'),
        ('good', 'Bom'),
        ('excellent', 'Excelente'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey('admin_app.Skill', on_delete=models.CASCADE, verbose_name='Habilidade')
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES, blank=True, null=True, verbose_name='Proficiência')
    years_of_exp = models.IntegerField(null=True, blank=True, verbose_name='Anos de Experiência')
    comment = models.TextField(blank=True, null=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Habilidade'
        verbose_name_plural = 'Habilidades'
        unique_together = ['employee', 'skill']

    def __str__(self):
        return f"{self.skill} - {self.employee}"


class EmployeeLanguage(models.Model):
    """Idiomas do funcionário"""
    FLUENCY_CHOICES = [
        ('poor', 'Fraco'),
        ('basic', 'Básico'),
        ('good', 'Bom'),
        ('mother_tongue', 'Língua Materna'),
    ]
    COMPETENCY_CHOICES = [
        ('reading', 'Leitura'),
        ('writing', 'Escrita'),
        ('speaking', 'Fala'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='languages')
    language = models.ForeignKey('admin_app.Language', on_delete=models.CASCADE, verbose_name='Idioma')
    fluency = models.CharField(max_length=30, choices=FLUENCY_CHOICES, blank=True, null=True, verbose_name='Fluência')
    competency = models.CharField(max_length=30, choices=COMPETENCY_CHOICES, blank=True, null=True, verbose_name='Competência')
    comment = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Idioma'
        verbose_name_plural = 'Idiomas'
        unique_together = ['employee', 'language']

    def __str__(self):
        return f"{self.language} - {self.employee}"


class EmployeeLicense(models.Model):
    """Licenças/Certificações do funcionário"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='licenses')
    license = models.ForeignKey('admin_app.License', on_delete=models.CASCADE, verbose_name='Licença')
    license_no = models.CharField(max_length=100, blank=True, null=True, verbose_name='Número da Licença')
    issued_date = models.DateField(null=True, blank=True, verbose_name='Data de Emissão')
    expiry_date = models.DateField(null=True, blank=True, verbose_name='Data de Validade')

    class Meta:
        verbose_name = 'Licença'
        verbose_name_plural = 'Licenças'

    def __str__(self):
        return f"{self.license} - {self.employee}"


class EmployeeMembership(models.Model):
    """Afiliações do funcionário"""
    SUBSCRIPTION_CHOICES = [
        ('individual', 'Individual'),
        ('employer', 'Empregador'),
        ('employer_individual', 'Empregador e Individual'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='memberships')
    membership = models.ForeignKey('admin_app.Membership', on_delete=models.CASCADE, verbose_name='Filiação')
    subscription_paid_by = models.CharField(max_length=30, choices=SUBSCRIPTION_CHOICES, null=True, blank=True, verbose_name='Pago por')
    subscription_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Taxa')
    subscription_currency = models.ForeignKey(
        'admin_app.CurrencyType', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Moeda'
    )
    subscription_commence_date = models.DateField(null=True, blank=True, verbose_name='Início')
    subscription_renewal_date = models.DateField(null=True, blank=True, verbose_name='Renovação')

    class Meta:
        verbose_name = 'Filiação'
        verbose_name_plural = 'Filiações'

    def __str__(self):
        return f"{self.membership} - {self.employee}"


class EmployeeSalary(models.Model):
    """Salário do funcionário"""
    PAYMENT_CHOICES = [
        ('cheque', 'Cheque'),
        ('cash', 'Dinheiro'),
        ('efts', 'Transferência'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salaries')
    salary_component = models.CharField(max_length=100, verbose_name='Componente Salarial')
    pay_grade = models.ForeignKey(
        'admin_app.PayGrade', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Faixa Salarial'
    )
    payment_frequency = models.CharField(max_length=50, blank=True, null=True, verbose_name='Frequência de Pagamento')
    currency = models.ForeignKey(
        'admin_app.CurrencyType', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Moeda'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Valor')
    comment = models.TextField(blank=True, null=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Salário'
        verbose_name_plural = 'Salários'

    def __str__(self):
        return f"{self.salary_component} - {self.employee}"


class EmpContract(models.Model):
    """Contrato de trabalho"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='contracts')
    contract_start_date = models.DateField(verbose_name='Início do Contrato')
    contract_end_date = models.DateField(null=True, blank=True, verbose_name='Fim do Contrato')
    contract_file = models.FileField(upload_to='contracts/', null=True, blank=True, verbose_name='Arquivo do Contrato')

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'

    def __str__(self):
        return f"Contrato {self.employee} ({self.contract_start_date})"


class TerminationReason(models.Model):
    """Motivos de desligamento"""
    name = models.CharField(max_length=200, unique=True, verbose_name='Motivo')

    class Meta:
        verbose_name = 'Motivo de Desligamento'
        verbose_name_plural = 'Motivos de Desligamento'

    def __str__(self):
        return self.name


class EmployeeTerminationRecord(models.Model):
    """Registro de desligamento"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='termination_records')
    termination_reason = models.ForeignKey(TerminationReason, on_delete=models.SET_NULL, null=True, verbose_name='Motivo')
    date = models.DateField(verbose_name='Data do Desligamento')
    note = models.TextField(blank=True, null=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Registro de Desligamento'
        verbose_name_plural = 'Registros de Desligamento'

    def __str__(self):
        return f"Desligamento de {self.employee} em {self.date}"


class EmployeeAttachment(models.Model):
    """Anexos do funcionário"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attachments')
    description = models.CharField(max_length=200, blank=True, null=True, verbose_name='Descrição')
    filename = models.CharField(max_length=200, verbose_name='Nome do Arquivo')
    file = models.FileField(upload_to='employee_attachments/', verbose_name='Arquivo')
    file_type = models.CharField(max_length=50, blank=True, null=True)
    file_size = models.IntegerField(null=True, blank=True)
    attached_by = models.ForeignKey(
        'core.OrangeUser', null=True, blank=True, on_delete=models.SET_NULL
    )
    attached_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'

    def __str__(self):
        return f"{self.filename} - {self.employee}"


class EmpUsTaxExemption(models.Model):
    """Isenção fiscal (US)"""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='tax_exemption')
    federal_status = models.CharField(max_length=50, blank=True, null=True)
    federal_exemptions = models.IntegerField(null=True, blank=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    state_status = models.CharField(max_length=50, blank=True, null=True)
    state_exemptions = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Isenção Fiscal'

    def __str__(self):
        return f"Tax Exemption - {self.employee}"


class OrgHierarchyRequest(models.Model):
    """Solicitações pendentes de alteração na estrutura organizacional (Organograma)"""
    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('APPROVED', 'Aprovado'),
        ('REJECTED', 'Rejeitado'),
    )
    
    requester = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='org_requests_made', verbose_name='Solicitante'
    )
    supervisor = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='incoming_org_requests', verbose_name='Novo Supervisor'
    )
    
    target_employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='org_hierarchy_changes', null=True, blank=True, verbose_name='Funcionário Alvo'
    )
    
    target_department = models.ForeignKey(
        'admin_app.Subunit', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Setor Alvo'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='Status')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Resolvido em')
    resolved_by = models.ForeignKey(
        'core.OrangeUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_org_requests', verbose_name='Resolvido Por'
    )

    class Meta:
        verbose_name = 'Solicitação de Organograma'
        verbose_name_plural = 'Solicitações de Organograma'
        ordering = ['-created_at']

    def __str__(self):
        target = self.target_employee.full_name if self.target_employee else f"Setor {self.target_department.name}"
        return f"Req: {target} -> {self.supervisor.full_name} ({self.status})"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Employee)
def sync_employee_supervisor_from_department(sender, instance, **kwargs):
    sub = instance.sub_division
    if sub:
        if sub.supervisor and sub.supervisor != instance:
            instance.supervisors.set([sub.supervisor])
        elif getattr(sub, 'supervisor', None) is None:
            instance.supervisors.clear()


from django.db.models.signals import m2m_changed

@receiver(m2m_changed, sender=Employee.supervisors.through)
def limit_supervisors_to_one(sender, instance, action, pk_set, **kwargs):
    """Garante de forma sólida blindada no backend que ninguém nunca terá mais de 1 supervisor."""
    if action == 'post_add':
        
        
        if instance.supervisors.count() > 1:
            
            if instance.sub_division and getattr(instance.sub_division, 'supervisor', None):
                correct_supervisor = instance.sub_division.supervisor
            else:
                correct_supervisor = instance.supervisors.last()
            
            
            instance.supervisors.clear()
            if correct_supervisor:
                instance.supervisors.add(correct_supervisor)

@receiver(post_save, sender=Employee)
def sync_user_active_status(sender, instance, **kwargs):
    """Desativa ou ativa o usuário correspondente de acordo com o status do funcionário."""
    try:
        if hasattr(instance, 'user') and instance.user:
            user = instance.user
            should_be_active = (instance.state == Employee.STATE_ACTIVE)
            if user.is_active != should_be_active:
                user.is_active = should_be_active
                user.save(update_fields=['is_active'])
    except Exception as e:
        pass
