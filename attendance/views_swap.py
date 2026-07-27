from django.http import JsonResponse
from core.decorators import require_module
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from pim.models import Employee
from attendance.models import ShiftSwapRequest, ShiftOverride
import json

@login_required
def swap_request_create(request):
    """Cria uma solicitação de troca de turno."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método inválido.'})
        
    try:
        body = json.loads(request.body)
        target_id = body.get('target_employee_id')
        date_str = body.get('date')
        reason = body.get('reason', '')
        
        if not target_id or not date_str:
            return JsonResponse({'success': False, 'message': 'Dados incompletos.'})
            
        my_emp = getattr(request.user, 'employee', None)
        if not my_emp:
            return JsonResponse({'success': False, 'message': 'Usuário não tem funcionário associado.'})
            
        if not my_emp.sub_division:
            return JsonResponse({'success': False, 'message': 'Você não tem um setor definido.'})
            
        if not my_emp.sub_division.allow_shift_swaps:
            return JsonResponse({'success': False, 'message': 'O seu departamento não permite trocas de turno.'})
            
        role_access_data = getattr(my_emp, 'get_role_access', lambda: None)()
        if role_access_data and not role_access_data.get('swap', True):
            return JsonResponse({'success': False, 'message': 'O seu cargo/perfil não tem permissão para realizar trocas de turno.'})
            
        target_emp = Employee.objects.filter(pk=target_id).first()
        if not target_emp:
            return JsonResponse({'success': False, 'message': 'Colega não encontrado.'})
            
        if target_emp.sub_division != my_emp.sub_division:
            return JsonResponse({'success': False, 'message': 'Só é permitido trocar turno com funcionários do mesmo setor.'})
            
      
        exists = ShiftSwapRequest.objects.filter(requester=my_emp, date=date_str).exclude(status__in=['APPROVED', 'REJECTED']).exists()
        if exists:
            return JsonResponse({'success': False, 'message': 'Você já possui uma solicitação pendente para este dia.'})
            
        ShiftSwapRequest.objects.create(
            requester=my_emp,
            target_employee=target_emp,
            date=date_str,
            reason=reason,
            status='PENDING_TARGET'
        )
        return JsonResponse({'success': True, 'message': 'Solicitação enviada! Aguardando o aceite do seu colega.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def swap_inbox_data(request):
    """Lista as solicitações pendentes para RH/Admin ou Supervisores."""
    user = request.user
    
    if user.is_admin():
        qs = ShiftSwapRequest.objects.filter(status='PENDING_HR').select_related('requester', 'target_employee')
    elif user.is_supervisor():
        from pim.utils import get_visible_employees
        visible_emps = get_visible_employees(user)
        qs = ShiftSwapRequest.objects.filter(status='PENDING_SUPERVISOR', requester__in=visible_emps).select_related('requester', 'target_employee')
    else:
        return JsonResponse({'success': False, 'message': 'Acesso negado.'}, status=403)
        
    data = []
    for req in qs:
        data.append({
            'id': req.id,
            'requester': req.requester.full_name,
            'target': req.target_employee.full_name,
            'date': req.date.strftime('%d/%m/%Y'),
            'reason': req.reason,
            'created_at': req.created_at.strftime('%d/%m/%Y %H:%M')
        })
    return JsonResponse({'success': True, 'requests': data})


@login_required
def swap_request_resolve(request):
    """Aprova ou rejeita uma solicitação e avança o estado."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método inválido.'})
        
    try:
        body = json.loads(request.body)
        req_id = body.get('request_id')
        action = body.get('action') 
        
        req_obj = ShiftSwapRequest.objects.get(pk=req_id)
        user = request.user
        emp = getattr(user, 'employee', None)
        
        if req_obj.status in ['APPROVED', 'REJECTED']:
            return JsonResponse({'success': False, 'message': 'Solicitação já finalizada.'})
            
        
        if action == 'REJ':
            can_reject = False
            if req_obj.status == 'PENDING_TARGET' and req_obj.target_employee == emp:
                can_reject = True
            elif req_obj.status == 'PENDING_SUPERVISOR' and user.is_supervisor():
                can_reject = True
            elif req_obj.status == 'PENDING_HR' and user.is_admin():
                can_reject = True
                
            if not can_reject:
                return JsonResponse({'success': False, 'message': 'Você não tem permissão para rejeitar no status atual.'})
                
            req_obj.status = 'REJECTED'
            req_obj.resolved_by = user
            req_obj.resolved_at = timezone.now()
            req_obj.save()
            return JsonResponse({'success': True, 'message': 'Solicitação Rejeitada e cancelada.'})
            
        
        if action == 'APP':
            
            if req_obj.status == 'PENDING_TARGET':
                if req_obj.target_employee != emp:
                    return JsonResponse({'success': False, 'message': 'Apenas o colega alvo pode aceitar essa etapa.'})
                req_obj.status = 'PENDING_SUPERVISOR'
                req_obj.save()
                return JsonResponse({'success': True, 'message': 'Troca aceita! Encaminhada para o Supervisor.'})
                
            
            elif req_obj.status == 'PENDING_SUPERVISOR':
                if not user.is_supervisor():
                    return JsonResponse({'success': False, 'message': 'Acesso restrito a supervisores.'})
                req_obj.status = 'PENDING_HR'
                req_obj.save()
                return JsonResponse({'success': True, 'message': 'Troca autorizada! Encaminhada para o RH.'})
                
            
            elif req_obj.status == 'PENDING_HR':
                if not user.is_admin():
                    return JsonResponse({'success': False, 'message': 'Acesso restrito ao RH.'})
                    
                maria = req_obj.requester
                joao = req_obj.target_employee
                
                if not maria.work_schedule or not joao.work_schedule:
                    return JsonResponse({'success': False, 'message': 'Ambos os funcionários precisam ter uma Escala Base cadastrada para gerar a troca.'})
                    
                from attendance.models import get_work_info_for_date
                maria_info = get_work_info_for_date(maria, req_obj.date)
                joao_info = get_work_info_for_date(joao, req_obj.date)
                
                ShiftOverride.objects.update_or_create(
                    employee=maria, date=req_obj.date,
                    defaults={'override_type': 'WORK', 'entry_time': joao_info.get('entry_time'), 'exit_time': joao_info.get('exit_time'), 'reason': f"Troca com {joao.first_name}", 'created_by': user}
                )
                
                ShiftOverride.objects.update_or_create(
                    employee=joao, date=req_obj.date,
                    defaults={'override_type': 'WORK', 'entry_time': maria_info.get('entry_time'), 'exit_time': maria_info.get('exit_time'), 'reason': f"Troca com {maria.first_name}", 'created_by': user}
                )
                
                req_obj.status = 'APPROVED'
                req_obj.resolved_by = user
                req_obj.resolved_at = timezone.now()
                req_obj.save()
                return JsonResponse({'success': True, 'message': 'Troca Aprovada com Sucesso e efetivada no banco de dados!'})
                
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_module('swap')
def swap_inbox_page(request):
    from django.shortcuts import render
    user = request.user
    emp = getattr(user, 'employee', None)
    
    
    pending_action = []
    qs = ShiftSwapRequest.objects.select_related('requester', 'target_employee').order_by('-created_at')
    
    if emp:
        
        pending_targets = qs.filter(target_employee=emp, status='PENDING_TARGET')
        pending_action.extend(pending_targets)
        
    if user.is_supervisor():
        from pim.utils import get_visible_employees
        visible_emps = get_visible_employees(user)
        pending_sups = qs.filter(status='PENDING_SUPERVISOR', requester__in=visible_emps)
        pending_action.extend(pending_sups)
        
    if user.is_admin():
        pending_hrs = qs.filter(status='PENDING_HR')
        pending_action.extend(pending_hrs)
        
    
    seen = set()
    pending_action_unique = []
    for p in pending_action:
        if p.id not in seen:
            seen.add(p.id)
            pending_action_unique.append(p)
            
    
    pending_action_unique.sort(key=lambda x: x.created_at, reverse=True)
    
    
    my_requests = []
    if emp:
        my_requests = qs.filter(requester=emp)
        
    
    colleagues = []
    if emp and emp.sub_division:
        from pim.models import Employee
        colleagues = Employee.objects.filter(sub_division=emp.sub_division, user__is_active=True).exclude(id=emp.id)
        
    
    combined = list(pending_action_unique)
    seen_ids = set(p.id for p in combined)
    for m in my_requests:
        if m.id not in seen_ids:
            combined.append(m)
            seen_ids.add(m.id)
            
    
    combined.sort(key=lambda x: x.created_at, reverse=True)
    
    return render(request, 'attendance/swap_inbox.html', {
        'swap_requests': combined,
        'colleagues': colleagues,
    })

@login_required
def api_swap_schedules(request, request_id):
    from django.http import JsonResponse
    from .models import ShiftSwapRequest, get_work_info_for_date
    import json
    
    try:
        req = ShiftSwapRequest.objects.get(id=request_id)
        
        
        emp = getattr(request.user, 'employee', None)
        if not (request.user.is_admin() or request.user.is_hr() or request.user.is_supervisor() or req.requester == emp or req.target_employee == emp):
            return JsonResponse({'success': False, 'message': 'Permissão negada.'}, status=403)
            
        target_date = req.date
        
        req_info = get_work_info_for_date(req.requester, target_date)
        tgt_info = get_work_info_for_date(req.target_employee, target_date)
        
        def format_info(employee, info):
            img_url = ''
            try:
                if employee.picture and employee.picture.picture:
                    img_url = employee.picture.picture.url
            except Exception:
                pass
                
            return {
                'name': employee.full_name,
                'image': img_url,
                'working': info.get('is_work_day', False),
                'in_time': info.get('entry_time').strftime('%H:%M') if info.get('entry_time') else '--:--',
                'out_time': info.get('exit_time').strftime('%H:%M') if info.get('exit_time') else '--:--',
                'status': 'Dia de Trabalho' if info.get('is_work_day') else 'Folga'
            }
            
        
        can_reject = False
        can_approve = False
        if req.status == 'PENDING_TARGET' and req.target_employee == emp:
            can_reject = True
            can_approve = True
        elif req.status == 'PENDING_SUPERVISOR' and request.user.is_supervisor():
            can_reject = True
            can_approve = True
        elif req.status == 'PENDING_HR' and request.user.is_admin():
            can_reject = True
            can_approve = True
            
        data = {
            'success': True,
            'date': target_date.strftime('%d/%m/%Y'),
            'status_display': req.get_status_display(),
            'status_code': req.status,
            'resolved_text': f"por {req.resolved_by.first_name}" if req.resolved_by else "",
            'can_approve': can_approve,
            'can_reject': can_reject,
            'requester': format_info(req.requester, req_info),
            'target': format_info(req.target_employee, tgt_info)
        }
        
        
        res = req.resolved_by
        t_sol = {'label': 'Solicitado', 'desc': 'Enviado', 'state': 'done', 'icon': 'bi-person-fill'}
        t_tgt = {'label': 'Colega Alvo', 'desc': 'Aguardando...', 'state': 'waiting', 'icon': 'bi-people-fill'}
        t_sup = {'label': 'Supervisão', 'desc': 'Aguardando...', 'state': 'waiting', 'icon': 'bi-person-check-fill'}
        t_hr = {'label': 'RH / Adm', 'desc': 'Aguardando...', 'state': 'waiting', 'icon': 'bi-shield-check'}
        
        s = req.status
        if s == 'PENDING_TARGET':
            t_tgt['state'] = 'current'
        elif s == 'PENDING_SUPERVISOR':
            t_tgt['state'] = 'done'; t_tgt['desc'] = 'Aceito'
            t_sup['state'] = 'current'
        elif s == 'PENDING_HR':
            t_tgt['state'] = 'done'; t_tgt['desc'] = 'Aceito'
            t_sup['state'] = 'done'; t_sup['desc'] = 'Pré-aprovado'
            t_hr['state'] = 'current'
        elif s == 'APPROVED':
            t_tgt['state'] = 'done'; t_tgt['desc'] = 'Aceito'
            t_sup['state'] = 'done'; t_sup['desc'] = 'Pré-aprovado'
            t_hr['state'] = 'done'; t_hr['desc'] = 'Aprovado \u2713'
        elif s == 'REJECTED':
            if res and res == req.target_employee.user:
                t_tgt['state'] = 'rejected'; t_tgt['desc'] = 'Recusado'
            elif res and res.is_supervisor() and not res.is_admin():
                t_tgt['state'] = 'done'; t_tgt['desc'] = 'Aceito'
                t_sup['state'] = 'rejected'; t_sup['desc'] = f'Recusado'
            else:
                t_tgt['state'] = 'done'; t_tgt['desc'] = 'Aceito'
                t_sup['state'] = 'done'; t_sup['desc'] = 'Pré-aprovado'
                t_hr['state'] = 'rejected'; t_hr['desc'] = 'Recusado'
                
        data['timeline'] = [t_sol, t_tgt, t_sup, t_hr]
        
        return JsonResponse(data)
    except ShiftSwapRequest.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Requisição não encontrada.'}, status=404)

