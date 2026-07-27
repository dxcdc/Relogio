from django.db import models


class Organization(models.Model):
    """Informações da organização"""
    name = models.CharField(max_length=100, verbose_name='Nome da Empresa')
    tax_id = models.CharField(max_length=30, blank=True, null=True, verbose_name='CNPJ/Tax ID')
    registration_number = models.CharField(max_length=30, blank=True, null=True, verbose_name='Nº de Registro')
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name='Telefone')
    fax = models.CharField(max_length=30, blank=True, null=True, verbose_name='Fax')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name='País')
    province = models.CharField(max_length=100, blank=True, null=True, verbose_name='Estado')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Cidade')
    zip_code = models.CharField(max_length=20, blank=True, null=True, verbose_name='CEP')
    street1 = models.CharField(max_length=100, blank=True, null=True, verbose_name='Endereço')
    street2 = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField(blank=True, null=True, verbose_name='Observações')
    logo = models.ImageField(upload_to='organization/', blank=True, null=True, verbose_name='Logo')

    class Meta:
        verbose_name = 'Organização'

    def __str__(self):
        return self.name


class LegalEntity(models.Model):
    """Empresas/Filiais (CNPJs separados)"""
    name = models.CharField(max_length=150, verbose_name='Razão Social / Nome Fantasia')
    tax_id = models.CharField(max_length=30, unique=True, verbose_name='CNPJ')
    registration_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='Inscrição Estadual/Municipal')
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name='Telefone')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    address = models.TextField(blank=True, null=True, verbose_name='Endereço Completo')
    note = models.TextField(blank=True, null=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Empresa/Filial'
        verbose_name_plural = 'Empresas/Filiais'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.tax_id})"


class Nationality(models.Model):
    """Nacionalidades"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Nacionalidade')

    class Meta:
        verbose_name = 'Nacionalidade'
        verbose_name_plural = 'Nacionalidades'
        ordering = ['name']

    def __str__(self):
        return self.name


class Country(models.Model):
    """Países"""
    name = models.CharField(max_length=100, verbose_name='País')
    code = models.CharField(max_length=3, unique=True, verbose_name='Código')

    class Meta:
        verbose_name = 'País'
        verbose_name_plural = 'Países'
        ordering = ['name']

    def __str__(self):
        return self.name


class Province(models.Model):
    """Estados/Províncias"""
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='provinces')
    name = models.CharField(max_length=100, verbose_name='Estado')
    code = models.CharField(max_length=10, verbose_name='Código')

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return f"{self.name} ({self.country})"


class City(models.Model):
    """Cidades"""
    name = models.CharField(max_length=150, verbose_name='Nome da Cidade')
    province = models.ForeignKey(
        Province, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Estado/Província'
    )

    class Meta:
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'
        ordering = ['name']

    def __str__(self):
        if self.province:
            return f"{self.name} - {self.province.code or self.province.name}"
        return self.name



class Location(models.Model):
    """Localizações físicas da empresa"""
    name = models.CharField(max_length=100, verbose_name='Nome')
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name='País')
    province = models.CharField(max_length=100, blank=True, null=True, verbose_name='Estado')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Cidade')
    neighborhood = models.CharField(max_length=100, blank=True, null=True, verbose_name='Bairro')
    address = models.TextField(blank=True, null=True, verbose_name='Endereço (Rua/Avenida)')
    address_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='Número')
    zip_code = models.CharField(max_length=20, blank=True, null=True, verbose_name='CEP')
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name='Telefone')
    fax = models.CharField(max_length=30, blank=True, null=True, verbose_name='Fax')
    note = models.TextField(blank=True, null=True, verbose_name='Observações')
    capacity = models.IntegerField(default=10, blank=True, null=True, verbose_name='Capacidade (Pessoas)')
    
    
    latitude = models.FloatField(null=True, blank=True, verbose_name='Latitude')
    longitude = models.FloatField(null=True, blank=True, verbose_name='Longitude')
    radius_meters = models.IntegerField(null=True, blank=True, verbose_name='Raio do Ponto (Metros)')
    allowed_ipv4 = models.CharField(max_length=50, null=True, blank=True, verbose_name='IP Público Permitido')
    is_meeting_room = models.BooleanField(default=False, verbose_name='É Sala de Reunião')

    class Meta:
        verbose_name = 'Localização'
        verbose_name_plural = 'Localizações'
        ordering = ['name']

    def __str__(self):
        return self.name


class Subunit(models.Model):
    """Departamentos/Unidades organizacionais (árvore)"""
    name = models.CharField(max_length=100, verbose_name='Nome')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='children', verbose_name='Unidade Pai'
    )
    supervisor = models.ForeignKey(
        'pim.Employee', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='managed_subunits', verbose_name='Supervisor do Departamento'
    )
    allow_shift_swaps = models.BooleanField(default=False, verbose_name='Permitir Trocas de Turno')

    class Meta:
        verbose_name = 'Unidade Organizacional'
        verbose_name_plural = 'Unidades Organizacionais'
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name


class JobTitle(models.Model):
    """Cargos"""
    title = models.CharField(max_length=100, unique=True, verbose_name='Cargo')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')
    note = models.TextField(blank=True, null=True, verbose_name='Observações')
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        ordering = ['title']

    def __str__(self):
        return self.title


class JobCategory(models.Model):
    """Categorias de cargo (EEO)"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Categoria')

    class Meta:
        verbose_name = 'Categoria de Cargo'
        verbose_name_plural = 'Categorias de Cargo'

    def __str__(self):
        return self.name


class EmploymentStatus(models.Model):
    """Status de emprego (CLT, PJ, etc.)"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Status')

    class Meta:
        verbose_name = 'Status de Emprego'
        verbose_name_plural = 'Status de Emprego'

    def __str__(self):
        return self.name


class PayGrade(models.Model):
    """Faixa salarial"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Faixa Salarial')

    class Meta:
        verbose_name = 'Faixa Salarial'
        verbose_name_plural = 'Faixas Salariais'

    def __str__(self):
        return self.name


class CurrencyType(models.Model):
    """Moedas"""
    id = models.CharField(max_length=10, primary_key=True, verbose_name='Código')
    name = models.CharField(max_length=70, verbose_name='Moeda')

    class Meta:
        verbose_name = 'Moeda'
        verbose_name_plural = 'Moedas'
        ordering = ['name']

    def __str__(self):
        return f"{self.id} - {self.name}"


class PayGradeCurrency(models.Model):
    """Faixas salariais por moeda"""
    pay_grade = models.ForeignKey(PayGrade, on_delete=models.CASCADE, related_name='currencies')
    currency = models.ForeignKey(CurrencyType, on_delete=models.CASCADE)
    min_salary = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name='Salário Mínimo')
    max_salary = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name='Salário Máximo')

    class Meta:
        verbose_name = 'Faixa Salarial por Moeda'
        unique_together = ['pay_grade', 'currency']

    def __str__(self):
        return f"{self.pay_grade} - {self.currency}"


class WorkShift(models.Model):
    """Turnos de trabalho"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Nome do Turno')
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=8, verbose_name='Horas por Dia')
    start_time = models.TimeField(verbose_name='Hora de Início')
    end_time = models.TimeField(verbose_name='Hora de Término')

    class Meta:
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'

    def __str__(self):
        return self.name


class Education(models.Model):
    """Níveis de educação"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Nível de Educação')

    class Meta:
        verbose_name = 'Nível de Educação'
        verbose_name_plural = 'Níveis de Educação'

    def __str__(self):
        return self.name


class Skill(models.Model):
    """Habilidades disponíveis"""
    name = models.CharField(max_length=120, unique=True, verbose_name='Habilidade')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')

    class Meta:
        verbose_name = 'Habilidade'
        verbose_name_plural = 'Habilidades'

    def __str__(self):
        return self.name


class Language(models.Model):
    """Idiomas disponíveis"""
    name = models.CharField(max_length=120, unique=True, verbose_name='Idioma')

    class Meta:
        verbose_name = 'Idioma'
        verbose_name_plural = 'Idiomas'

    def __str__(self):
        return self.name


class License(models.Model):
    """Tipos de licença/certificação"""
    name = models.CharField(max_length=200, unique=True, verbose_name='Licença')

    class Meta:
        verbose_name = 'Licença'
        verbose_name_plural = 'Licenças'

    def __str__(self):
        return self.name


class Membership(models.Model):
    """Tipos de filiação/associação"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Filiação')

    class Meta:
        verbose_name = 'Tipo de Filiação'
        verbose_name_plural = 'Tipos de Filiação'

    def __str__(self):
        return self.name


class EmailNotification(models.Model):
    """Notificações de email"""
    name = models.CharField(max_length=100, verbose_name='Notificação')
    description = models.TextField(blank=True, null=True)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Notificação de Email'
        verbose_name_plural = 'Notificações de Email'

    def __str__(self):
        return self.name

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Subunit)
def sync_all_employees_when_department_supervisor_changes(sender, instance, **kwargs):
    supervisor = instance.supervisor
    for emp in instance.employee_set.all():
        if supervisor and emp != supervisor:
            emp.supervisors.set([supervisor])
        elif not supervisor:
            emp.supervisors.clear()

