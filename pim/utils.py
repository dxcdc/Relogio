from django.db.models import Q
from .models import Employee


def get_visible_employees(user):
    """
    Retorna o queryset de funcionários que o usuário logado tem permissão de ver.

    Regras:
    - Admin     → vê todos os funcionários da empresa
    - Supervisor → vê apenas funcionários do seu setor (sub_division),
                   INCLUINDO o próprio supervisor como funcionário
    - ESS       → só o próprio funcionário (tratado nas views individualmente)
    """
    if user.role in ['Admin', 'HR']:
        return Employee.objects.all()

    if user.role == 'Supervisor':
        my_employee = getattr(user, 'employee', None)
        if not my_employee:
            return Employee.objects.none()

        sub = my_employee.sub_division

        if sub:
            
            return Employee.objects.filter(
                Q(sub_division=sub) | Q(supervisors=my_employee) | Q(pk=my_employee.pk)
            ).distinct()
        else:
            
            return Employee.objects.filter(
                Q(supervisors=my_employee) | Q(pk=my_employee.pk)
            ).distinct()

    
    my_employee = getattr(user, 'employee', None)
    if my_employee:
        return Employee.objects.filter(pk=my_employee.pk)
    return Employee.objects.none()


def supervisor_can_access_employee(user, employee):
    """
    Verifica se um usuário Supervisor tem permissão de acessar
    o perfil de um funcionário específico.

    - Admin/HR sempre pode.
    - Supervisor pode acessar funcionários do próprio setor OU o próprio perfil.
    - ESS só pode acessar o próprio perfil.
    """
    if user.is_admin():
        return True

    my_employee = getattr(user, 'employee', None)
    if not my_employee:
        return False

    
    if my_employee.pk == employee.pk:
        return True

    if user.role == 'Supervisor':
        
        if employee.supervisors.filter(pk=my_employee.pk).exists():
            return True
            
        
        sub = my_employee.sub_division
        if sub and employee.sub_division == sub:
            return True
            
        return False

    
    return False


import re
import unicodedata
import secrets

def generate_uppercase_username(first_name, last_name):
    """
    Gera um username em LETRAS MAIÚSCULAS seguindo a lógica em cascata:
    1. Apenas o Primeiro Nome (ex: JOAO)
    2. Primeiro Nome + Primeiro Sobrenome (ex: JOAO.SILVA)
    3. Primeiro Nome + Sobrenomes Combinados (ex: JOAO.SILVASANTOS)
    4. Adiciona número incremental em caso de colisões (ex: JOAO.SILVASANTOS1)
    """
    # Normaliza e remove acentos
    fn = unicodedata.normalize('NFKD', first_name).encode('ASCII', 'ignore').decode('utf-8').upper()
    ln = unicodedata.normalize('NFKD', last_name).encode('ASCII', 'ignore').decode('utf-8').upper()
    
    # Mantém apenas caracteres alfanuméricos e espaços
    fn = re.sub(r'[^A-Z0-9 ]', '', fn).strip()
    ln = re.sub(r'[^A-Z0-9 ]', '', ln).strip()
    
    fn_parts = [p for p in fn.split() if p]
    ln_parts = [p for p in ln.split() if p]
    
    first = fn_parts[0] if fn_parts else "USER"
    
    from core.models import OrangeUser
    
    # 1. Tenta apenas o primeiro nome
    username = first
    if not OrangeUser.objects.filter(username=username).exists():
        return username
        
    # 2. Tenta Primeiro Nome + Primeiro Sobrenome
    if ln_parts:
        username = f"{first}.{ln_parts[0]}"
        if not OrangeUser.objects.filter(username=username).exists():
            return username
            
    # 3. Tenta Primeiro Nome + Sobrenome Completo
    if len(ln_parts) > 1:
        full_last = "".join(ln_parts)
        username = f"{first}.{full_last}"
        if not OrangeUser.objects.filter(username=username).exists():
            return username
            
    # 4. Adiciona número em caso de persistir a colisão
    base_username = username
    counter = 1
    while OrangeUser.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
        
    return username

def generate_random_temp_password():
    """Gera uma senha provisória aleatória e limpa no formato NL-XXXX-YYYY"""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789" # Remove letras confusas como O, I, 1, 0
    part1 = "".join(secrets.choice(chars) for _ in range(4))
    part2 = "".join(secrets.choice(chars) for _ in range(4))
    return f"NL-{part1}-{part2}"
