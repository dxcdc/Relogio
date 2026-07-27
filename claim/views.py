import os
from django.shortcuts import render, get_object_or_404, redirect
from pim.views import redirect_with_popup
from django.contrib.auth.decorators import login_required
from core.decorators import require_module
from django.contrib import messages
from .models import ClaimRequest, ClaimEvent, ExpenseType, ClaimExpense, ClaimAttachment
from django import forms


from pim.models import Employee

class ClaimRequestForm(forms.ModelForm):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        label="Funcionário",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = ClaimRequest
        fields = ['employee', 'claim_event', 'currency', 'reference_id', 'description']
        widgets = {
            'claim_event': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'reference_id': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        allowed_employees = kwargs.pop('allowed_employees', None)
        super().__init__(*args, **kwargs)
        if allowed_employees is not None:
            self.fields['employee'].queryset = allowed_employees


class ClaimExpenseForm(forms.ModelForm):
    class Meta:
        model = ClaimExpense
        fields = ['expense_type', 'expense_date', 'amount', 'note']
        widgets = {
            'expense_type': forms.Select(attrs={'class': 'form-select'}),
            'expense_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ClaimEventForm(forms.ModelForm):
    class Meta:
        model = ClaimEvent
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ExpenseTypeForm(forms.ModelForm):
    class Meta:
        model = ExpenseType
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }




@login_required
@require_module('claim')
def claim_list(request):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        return redirect_with_popup(request, 'dashboard')
        
    user = request.user
    from pim.utils import get_visible_employees
    visible_emps = get_visible_employees(user)
    
    from django.db.models import Q
    q = request.GET.get('q', '').strip()
    
    claims = ClaimRequest.objects.filter(employee__in=visible_emps)
    if q:
        claims = claims.filter(
            Q(employee__first_name__icontains=q) | 
            Q(employee__last_name__icontains=q) |
            Q(reference_id__icontains=q)
        )
        
    claims = claims.select_related(
        'employee', 'claim_event', 'currency'
    ).prefetch_related('expenses__expense_type', 'attachments').order_by('-created_at')
    
    form = ClaimRequestForm(allowed_employees=visible_emps)
    return render(request, 'claim/claim_list.html', {'claims': claims, 'form': form, 'q': q})


@login_required
@require_module('claim')
def claim_create(request):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        messages.error(request, 'Apenas gestores podem cadastrar reembolsos.')
        return redirect_with_popup(request, 'dashboard')

    from pim.utils import get_visible_employees
    visible_emps = get_visible_employees(request.user)
    
    if request.method == 'POST':
        form = ClaimRequestForm(request.POST, allowed_employees=visible_emps)
        if form.is_valid():
            claim = form.save()
            messages.success(request, 'Solicitação criada!')
            return redirect_with_popup(request, 'claim_detail', pk=claim.pk)
    else:
        form = ClaimRequestForm(allowed_employees=visible_emps)
        my_emp = getattr(request.user, 'employee', None)
        if my_emp and visible_emps.filter(pk=my_emp.pk).exists():
            form.initial['employee'] = my_emp.pk

    return render(request, 'claim/claim_form.html', {'form': form, 'title': 'Nova Solicitação'})


@login_required
def claim_detail(request, pk):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        return redirect_with_popup(request, 'dashboard')
        
    claim = get_object_or_404(
        ClaimRequest.objects.prefetch_related('expenses__expense_type', 'attachments'), pk=pk
    )
    
    from pim.utils import get_visible_employees
    visible_emps = get_visible_employees(request.user)
    
    if not visible_emps.filter(pk=claim.employee_id).exists():
        messages.error(request, 'Acesso negado.')
        return redirect_with_popup(request, 'claim_list')

    expense_form = ClaimExpenseForm()
    expense_types = ExpenseType.objects.filter(is_active=True).order_by('name')
    return render(request, 'claim/claim_detail.html', {
        'claim': claim,
        'expense_form': expense_form,
        'expense_types': expense_types,
    })


@login_required
def claim_submit(request, pk):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        return redirect_with_popup(request, 'dashboard')
        
    from django.utils import timezone
    claim = get_object_or_404(ClaimRequest, pk=pk)
    
    from pim.utils import get_visible_employees
    visible_emps = get_visible_employees(request.user)
    
    if not visible_emps.filter(pk=claim.employee_id).exists():
        messages.error(request, 'Você não tem permissão para enviar esta solicitação.')
        return redirect_with_popup(request, 'claim_list')

    claim.status = ClaimRequest.STATUS_SUPERVISOR_APPROVED
    claim.submitted_date = timezone.now().date()
    claim.save()
    messages.success(request, 'Solicitação enviada para o RH com sucesso!')
    return redirect_with_popup(request, 'claim_detail', pk=pk)


@login_required
def claim_approve(request, pk):
    """Etapa 1 — Supervisor pré-aprova: SUBMITTED → SUPERVISOR_APPROVED."""
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect_with_popup(request, 'dashboard')
    claim = get_object_or_404(ClaimRequest, pk=pk)
    if claim.status != ClaimRequest.STATUS_SUBMITTED:
        messages.warning(request, 'Esta solicitação não está aguardando aprovação do supervisor.')
        return redirect_with_popup(request, 'leave_list')
    claim.status = ClaimRequest.STATUS_SUPERVISOR_APPROVED
    claim.save()
    messages.success(request, 'Reembolso pré-aprovado! Aguardando aprovação final do RH.')
    return redirect_with_popup(request, 'leave_list')


@login_required
def claim_final_approve(request, pk):
    """Etapa 2 — RH/Admin faz a aprovação final: SUPERVISOR_APPROVED → APPROVED."""
    if not (request.user.is_admin() or getattr(request.user, 'is_hr', lambda: False)()):
        messages.error(request, 'Acesso restrito a RH/Administradores.')
        return redirect_with_popup(request, 'dashboard')
    claim = get_object_or_404(ClaimRequest, pk=pk)
    if claim.status != ClaimRequest.STATUS_SUPERVISOR_APPROVED:
        messages.warning(request, 'Esta solicitação não está aguardando aprovação do RH.')
        return redirect_with_popup(request, 'leave_list')
    claim.status = ClaimRequest.STATUS_APPROVED
    claim.save()
    messages.success(request, 'Reembolso aprovado definitivamente!')
    return redirect_with_popup(request, 'leave_list')


@login_required
def claim_reject(request, pk):
    """Rejeição em qualquer etapa (Supervisor ou RH/Admin)."""
    if not (request.user.is_supervisor() or request.user.is_admin()):
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect_with_popup(request, 'dashboard')
    claim = get_object_or_404(ClaimRequest, pk=pk)
    allowed = {ClaimRequest.STATUS_SUBMITTED, ClaimRequest.STATUS_SUPERVISOR_APPROVED}
    if claim.status not in allowed:
        messages.warning(request, 'Esta solicitação não pode ser rejeitada neste estado.')
        return redirect_with_popup(request, 'leave_list')
    reason = request.POST.get('rejection_reason', '').strip()
    claim.status = ClaimRequest.STATUS_REJECTED
    claim.rejection_reason = reason or None
    claim.save()
    messages.warning(request, 'Reembolso rejeitado.')
    return redirect_with_popup(request, 'leave_list')



@login_required
def claim_delete(request, pk):
    """Exclui (Cancela) a solicitação caso ainda seja um rascunho (INITIATED)."""
    if not (request.user.is_admin() or request.user.is_supervisor()):
        return redirect_with_popup(request, 'dashboard')
        
    claim = get_object_or_404(ClaimRequest, pk=pk)
    
    from pim.utils import get_visible_employees
    visible_emps = get_visible_employees(request.user)
    if not visible_emps.filter(pk=claim.employee_id).exists():
        messages.error(request, 'Você não tem permissão para cancelar esta solicitação.')
        return redirect_with_popup(request, 'claim_list')
        
    if claim.status != ClaimRequest.STATUS_INITIATED:
        messages.error(request, 'Apenas solicitações em rascunho podem ser canceladas e apagadas.')
        return redirect_with_popup(request, 'claim_list')
        
    claim.delete()
    messages.success(request, 'Rascunho de solicitação excluído com sucesso.')
    return redirect_with_popup(request, 'claim_list')




@login_required
def expense_add(request, claim_pk):
    claim = get_object_or_404(ClaimRequest, pk=claim_pk)
    
    from pim.utils import get_visible_employees
    visible_emps = get_visible_employees(request.user)
    if not visible_emps.filter(pk=claim.employee_id).exists():
        messages.error(request, 'Acesso negado.')
        return redirect_with_popup(request, 'claim_list')
        
    if claim.status != ClaimRequest.STATUS_INITIATED:
        messages.error(request, 'Despesas só podem ser adicionadas em rascunhos.')
        return redirect_with_popup(request, 'claim_detail', pk=claim_pk)
        
    if request.method == 'POST':
        form = ClaimExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            if expense.amount < 0:
                messages.error(request, 'O valor não pode ser negativo.')
            else:
                expense.claim_request = claim
                expense.save()
                messages.success(request, 'Despesa adicionada!')
                return redirect_with_popup(request, 'claim_detail', pk=claim_pk)
    else:
        form = ClaimExpenseForm()
    return render(request, 'claim/claim_form.html', {'form': form, 'title': 'Adicionar Despesa'})


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(ClaimExpense, pk=pk)
    claim = expense.claim_request
    
    from pim.utils import get_visible_employees
    if not get_visible_employees(request.user).filter(pk=claim.employee_id).exists():
        messages.error(request, 'Acesso negado.')
        return redirect_with_popup(request, 'claim_list')
        
    if claim.status != ClaimRequest.STATUS_INITIATED:
        messages.error(request, 'Despesas só podem ser editadas em rascunhos.')
        return redirect_with_popup(request, 'claim_detail', pk=claim.pk)

    if request.method == 'POST':
        form = ClaimExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            exp = form.save(commit=False)
            if exp.amount < 0:
                messages.error(request, 'O valor não pode ser negativo.')
            else:
                exp.save()
                messages.success(request, 'Despesa atualizada!')
                return redirect_with_popup(request, 'claim_detail', pk=claim.pk)
    else:
        form = ClaimExpenseForm(instance=expense)
    return render(request, 'claim/claim_form.html', {'form': form, 'title': 'Editar Despesa'})


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(ClaimExpense, pk=pk)
    claim = expense.claim_request
    
    from pim.utils import get_visible_employees
    if not get_visible_employees(request.user).filter(pk=claim.employee_id).exists():
        messages.error(request, 'Acesso negado.')
        return redirect_with_popup(request, 'claim_list')
        
    if claim.status != ClaimRequest.STATUS_INITIATED:
        messages.error(request, 'Apenas rascunhos podem sofrer alterações.')
        return redirect_with_popup(request, 'claim_detail', pk=claim.pk)

    expense.delete()
    messages.success(request, 'Despesa removida!')
    return redirect_with_popup(request, 'claim_detail', pk=claim.pk)




@login_required
def event_list(request):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect_with_popup(request, 'dashboard')
    events = ClaimEvent.objects.filter(is_active=True)
    return render(request, 'claim/event_list.html', {'events': events})


@login_required
def event_create(request):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = ClaimEventForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento criado!')
            return redirect_with_popup(request, 'event_list')
    else:
        form = ClaimEventForm()
    return render(request, 'claim/claim_form.html', {'form': form, 'title': 'Novo Evento'})


@login_required
def event_edit(request, pk):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect_with_popup(request, 'dashboard')
    event = get_object_or_404(ClaimEvent, pk=pk)
    if request.method == 'POST':
        form = ClaimEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento atualizado!')
            return redirect_with_popup(request, 'event_list')
    else:
        form = ClaimEventForm(instance=event)
    return render(request, 'claim/claim_form.html', {'form': form, 'title': 'Editar Evento'})


@login_required
def event_delete(request, pk):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect_with_popup(request, 'dashboard')
    event = get_object_or_404(ClaimEvent, pk=pk)
    event.is_active = False
    event.save()
    messages.success(request, 'Evento desativado.')
    return redirect_with_popup(request, 'event_list')




@login_required
def expense_type_list(request):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect_with_popup(request, 'dashboard')
    types = ExpenseType.objects.filter(is_active=True)
    return render(request, 'claim/expense_type_list.html', {'types': types})


@login_required
def expense_type_create(request):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect_with_popup(request, 'dashboard')
    if request.method == 'POST':
        form = ExpenseTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de despesa criado!')
            return redirect_with_popup(request, 'expense_type_list')
    else:
        form = ExpenseTypeForm()
    return render(request, 'claim/claim_form.html', {'form': form, 'title': 'Novo Tipo de Despesa'})


@login_required
def expense_type_edit(request, pk):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect_with_popup(request, 'dashboard')
    et = get_object_or_404(ExpenseType, pk=pk)
    if request.method == 'POST':
        form = ExpenseTypeForm(request.POST, instance=et)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de despesa atualizado!')
            return redirect_with_popup(request, 'expense_type_list')
    else:
        form = ExpenseTypeForm(instance=et)
    return render(request, 'claim/claim_form.html', {'form': form, 'title': 'Editar Tipo de Despesa'})


@login_required
def expense_type_delete(request, pk):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect_with_popup(request, 'dashboard')
    et = get_object_or_404(ExpenseType, pk=pk)
    et.is_active = False
    et.save()
    messages.success(request, 'Tipo de despesa desativado.')
    return redirect_with_popup(request, 'expense_type_list')




@login_required
def attachment_upload(request, claim_pk):
    claim = get_object_or_404(ClaimRequest, pk=claim_pk)
    
    from pim.utils import get_visible_employees
    if not get_visible_employees(request.user).filter(pk=claim.employee_id).exists():
        messages.error(request, 'Acesso negado.')
        return redirect_with_popup(request, 'claim_list')
        
    if claim.status != ClaimRequest.STATUS_INITIATED:
        messages.error(request, 'Comprovantes só podem ser anexados a rascunhos.')
        return redirect_with_popup(request, 'claim_detail', pk=claim_pk)

    if request.method == 'POST':
        files = request.FILES.getlist('attachments')
        description = request.POST.get('description', '').strip()
        if not files:
            messages.warning(request, 'Nenhum arquivo selecionado.')
        else:
            allowed_exts = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.webp'}
            saved_count = 0
            for f in files:
                ext = os.path.splitext(f.name)[1].lower()
                if ext not in allowed_exts:
                    messages.error(request, f'Extensão {ext} não permitida.')
                    continue
                if f.size > 10 * 1024 * 1024:
                    messages.error(request, f'Arquivo {f.name} ultrapassa 10MB.')
                    continue
                    
                ClaimAttachment.objects.create(
                    claim_request=claim,
                    file=f,
                    file_name=f.name,
                    description=description or None,
                )
                saved_count += 1
            if saved_count > 0:
                messages.success(request, f'{saved_count} anexo(s) enviado(s) com sucesso!')
    return redirect_with_popup(request, 'claim_detail', pk=claim_pk)


@login_required
def attachment_delete(request, pk):
    attachment = get_object_or_404(ClaimAttachment, pk=pk)
    claim = attachment.claim_request
    
    from pim.utils import get_visible_employees
    if not get_visible_employees(request.user).filter(pk=claim.employee_id).exists():
        messages.error(request, 'Acesso negado.')
        return redirect_with_popup(request, 'claim_list')
        
    if claim.status != ClaimRequest.STATUS_INITIATED:
        messages.error(request, 'Apenas rascunhos podem ter anexos removidos.')
        return redirect_with_popup(request, 'claim_detail', pk=claim.pk)

    try:
        if attachment.file and os.path.isfile(attachment.file.path):
            os.remove(attachment.file.path)
    except Exception:
        pass
    attachment.delete()
    messages.success(request, 'Anexo removido.')
    return redirect_with_popup(request, 'claim_detail', pk=claim.pk)
