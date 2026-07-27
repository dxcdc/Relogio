from django.shortcuts import render, redirect, get_object_or_404
from core.decorators import require_module

def redirect_with_popup(request, *args, **kwargs):
    from django.shortcuts import redirect
    response = redirect(*args, **kwargs)
    if getattr(request, 'GET', {}).get('popup') or getattr(request, 'POST', {}).get('popup'):
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(response.url)
        new_query = parsed.query + ('&' if parsed.query else '') + 'popup=1'
        new_url = urlunparse(parsed._replace(query=new_query))
        response['Location'] = new_url
    return response

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import AttendanceRecord, WorkSchedule, AttendanceAdjustment, ShiftPattern, ShiftPatternDay, EmployeeShiftAssignment, ShiftOverride, get_work_info_for_date, PendingPunchRequest
from pim.models import Employee
from pim.utils import get_visible_employees
from django.db.models import Q
from django import forms


WEEKDAY_CHOICES = [
    (0, 'Segunda-feira'),
    (1, 'Terça-feira'),
    (2, 'Quarta-feira'),
    (3, 'Quinta-feira'),
    (4, 'Sexta-feira'),
    (5, 'Sábado'),
    (6, 'Domingo'),
]

from .models import WorkScheduleDay

class WorkScheduleForm(forms.ModelForm):
    class Meta:
        model = WorkSchedule
        fields = ['name', 'tolerance_minutes', 'automatic_break_minutes', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Jornada 8h...'}),
            'tolerance_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'automatic_break_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Ex: 15'}),
        }


@login_required
def attendance_list(request):
    user = request.user
    q = request.GET.get('q', '').strip()
    emp_id = request.GET.get('emp_id', '')
    month_val = request.GET.get('month_val', '')
    dept_id = request.GET.get('dept_id', '')
    
    from pim.utils import get_visible_employees
    from admin_app.models import Subunit
    
    visible_emp = get_visible_employees(user) if user.is_supervisor() else None
    
    
    
    if user.is_admin():
        departments = Subunit.objects.all().order_by('name')
    elif user.is_supervisor() and hasattr(user, 'employee') and user.employee.sub_division:
        departments = Subunit.objects.filter(pk=user.employee.sub_division.pk)
    else:
        departments = None

    if user.is_supervisor():
        records = AttendanceRecord.objects.filter(employee__in=visible_emp)
    else:
        emp = getattr(user, 'employee', None)
        records = AttendanceRecord.objects.filter(employee=emp) if emp else AttendanceRecord.objects.none()

    if q:
        records = records.filter(
            Q(employee__first_name__icontains=q) | 
            Q(employee__last_name__icontains=q) |
            Q(employee__employee_id__icontains=q)
        )
        
    if emp_id:
        records = records.filter(employee_id=emp_id)
        
    if dept_id:
        records = records.filter(employee__sub_division_id=dept_id)
        
    if month_val:
        try:
            y, m = month_val.split('-')
            records = records.filter(date__year=int(y), date__month=int(m))
        except:
            pass
            
    if request.GET.get('export') == 'excel':
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="Ponto_Equipe.csv"'
        
        writer = csv.writer(response, delimiter=';')
        
        records_q = records.order_by('-date')
        
        
        max_punches = 4
        for r in records_q:
            cnt = r.punches.count()
            if cnt > max_punches:
                max_punches = cnt
                
        
        headers = ['Departamento', 'Funcionário', 'Data']
        for i in range(max_punches):
            if i % 2 == 0:
                headers.append(f'Entrada {(i//2) + 1}')
            else:
                headers.append(f'Saída {(i//2) + 1}')
        headers.extend(['Total Trabalhado', 'Status GPS', 'Atraso'])
        
        writer.writerow(headers)
        
        records_q_list = list(records_q.prefetch_related('punches'))
        from attendance.models import get_work_info_for_date_bulk
        unique_dates = set(r.date for r in records_q_list)
        employees_in_records = list(set(r.employee for r in records_q_list))
        bulk_info = {}
        for d in unique_dates:
            bulk_info[d] = get_work_info_for_date_bulk(employees_in_records, d)

        for r in records_q_list:
            r._prefetched_work_info = bulk_info.get(r.date, {}).get(r.employee_id, {})
            punches_qs = r.punches.all().order_by('timestamp_user')
            punch_times = [p.timestamp_user.strftime('%H:%M') for p in punches_qs]
            is_flagged = any(p.is_flagged_location for p in punches_qs)
                
            while len(punch_times) < max_punches:
                punch_times.append('')
                
            row = [
                r.employee.sub_division.name if r.employee.sub_division else '',
                r.employee.full_name or '',
                r.date.strftime('%d/%m/%Y'),
            ]
            row.extend(punch_times)
            row.extend([
                str(r.net_hours_worked) if r.net_hours_worked else '',
                'Indisponível' if is_flagged else 'Válido',
                'Sim' if r.is_late else 'Não'
            ])
            writer.writerow(row)
            
        return response
        
    records = list(records.select_related('employee', 'employee__sub_division').prefetch_related('punches').order_by('-date')[:100])
    employees_in_records = list(set(r.employee for r in records))
    unique_dates = sorted(set(r.date for r in records))

    if employees_in_records and unique_dates:
        if len(employees_in_records) == 1:
            # Caso mais comum (funcionário vendo os próprios registros):
            # get_work_info_for_date_range = 5 queries totais para todo o período
            from attendance.models import get_work_info_for_date_range
            emp_obj = employees_in_records[0]
            range_info = get_work_info_for_date_range(emp_obj, unique_dates[0], unique_dates[-1])
            for r in records:
                r._prefetched_work_info = range_info.get(r.date, {})
        else:
            # Supervisor/Admin vendo múltiplos funcionários
            from attendance.models import get_work_info_for_date_bulk
            bulk_info = {}
            for d in unique_dates:
                bulk_info[d] = get_work_info_for_date_bulk(employees_in_records, d)
            for r in records:
                r._prefetched_work_info = bulk_info.get(r.date, {}).get(r.employee_id, {})

    context = {
        'records': records, 
        'q': q, 
        'emp_id': str(emp_id), 
        'month_val': month_val,
        'dept_id': str(dept_id),
        'departments': departments,
        'visible_emps': visible_emp.order_by('first_name') if visible_emp else None
    }
    return render(request, 'attendance/attendance_list.html', context)



@login_required
def punch_action(request):
    import base64
    import uuid
    from django.core.files.base import ContentFile
    from django.shortcuts import redirect
    from django.contrib import messages
    from django.utils import timezone
    from ipware import get_client_ip
    from geopy.distance import geodesic
    from .models import get_work_info_for_date, AttendanceRecord, AttendancePunch, PendingPunchRequest

    if request.method != 'POST':
        return redirect('attendance_my')
        
    user = request.user
    emp = getattr(user, 'employee', None)
    if not emp:
        messages.error(request, 'Usuário não vinculado a um funcionário.')
        return redirect('dashboard')
        
    now = timezone.now()
    local_now = timezone.localtime(now)
    local_date = local_now.date()
    
    work_info = get_work_info_for_date(emp, local_date)
    if work_info.get('source') == 'leave' and not work_info.get('is_work_day'):
        messages.error(request, 'Ação bloqueada: Você está de licença no dia de hoje.')
        return redirect(request.META.get('HTTP_REFERER') or 'attendance_my')

    note = request.POST.get('note', '').strip()[:300]
    lat = request.POST.get('lat')
    lng = request.POST.get('lng')
    
    client_ip, is_routable = get_client_ip(request)
    is_valid_location = False
    fraud_details = f"IP detectado: {client_ip}. Coordenadas: {lat}, {lng}. Locais não conferem."
    locations = emp.locations.all()
    if not locations.exists():
        
        is_valid_location = True
        fraud_details = None
    else:
        for loc in locations:
            has_ip  = bool(loc.allowed_ipv4 and loc.allowed_ipv4.strip())
            has_gps = bool(loc.latitude and loc.longitude and loc.radius_meters)

            ip_ok  = False
            gps_ok = False
            gps_dist_msg = ""

            if has_ip:
                ip_ok = (client_ip == loc.allowed_ipv4.strip())

            if has_gps and lat and lng:
                try:
                    dist = geodesic((float(lat), float(lng)), (loc.latitude, loc.longitude)).meters
                    gps_ok = dist <= loc.radius_meters
                    if not gps_ok:
                        gps_dist_msg = f"Distância até '{loc.name}': {dist:.2f}m (Permitido: {loc.radius_meters}m)."
                except Exception as e:
                    gps_dist_msg = f"Erro GPS: {str(e)}"

            
            
            
            
            
            if has_ip and has_gps:
                loc_valid = ip_ok and gps_ok
                if not loc_valid:
                    reasons = []
                    if not ip_ok:
                        reasons.append(f"IP '{client_ip}' não autorizado")
                    if not gps_ok:
                        reasons.append(gps_dist_msg or "GPS fora do perímetro")
                    fraud_details = f"[{loc.name}] " + " | ".join(reasons)
            elif has_ip:
                loc_valid = ip_ok
                if not loc_valid:
                    fraud_details = f"[{loc.name}] IP '{client_ip}' não autorizado (esperado: {loc.allowed_ipv4.strip()})"
            elif has_gps:
                loc_valid = gps_ok
                if not loc_valid:
                    fraud_details = f"[{loc.name}] {gps_dist_msg}"
            else:
                loc_valid = True  

            if loc_valid:
                is_valid_location = True
                fraud_details = None
                break
    
    photo_b64 = request.POST.get('photo_base64', '')
    photo_file = None
    if photo_b64:
        try:
            format_str, imgstr = photo_b64.split(';base64,')
            ext = format_str.split('/')[-1].lower().strip()
            ALLOWED_PHOTO_EXTENSIONS = ['jpeg', 'jpg', 'png', 'webp']
            if ext not in ALLOWED_PHOTO_EXTENSIONS:
                ext = 'jpg'  
            photo_file = ContentFile(base64.b64decode(imgstr), name=f"{emp.id}_punch_{uuid.uuid4().hex[:8]}.{ext}")
        except Exception:
            pass

    record_today, created = AttendanceRecord.objects.get_or_create(
        employee=emp, date=local_date
    )
    
    current_state = record_today.current_state
    next_action_type = 'IN' if current_state in [None, 'OUT'] else 'OUT'

    
    
    needs_photo = (record_today.punches.count() == 0)
    is_invalid = (needs_photo and not photo_file) or not is_valid_location
    
    try:
        lat_f = float(lat) if lat else None
        lng_f = float(lng) if lng else None
    except (TypeError, ValueError):
        lat_f = lng_f = None

    

    if is_invalid:
        PendingPunchRequest.objects.create(
            employee=emp,
            action_type=next_action_type,
            requested_at=now,
            photo=photo_file,
            lat=lat_f,
            lng=lng_f,
            fail_reason=fraud_details or "Foto obrigatória ausente",
            linked_record=record_today
        )
        messages.warning(request, "Ponto com ressalvas. Salvo como PENDENTE para aprovação do supervisor.")
        return redirect(request.META.get('HTTP_REFERER') or 'dashboard')

    
    punch = AttendancePunch.objects.create(
        attendance_record=record_today,
        punch_type=next_action_type,
        timestamp_utc=now,
        timestamp_user=local_now,
        note=note,
        photo=photo_file,
        latitude=lat_f,
        longitude=lng_f,
        ip_address=client_ip,
        location_address=None,  
        is_flagged_location=not is_valid_location,
        fraud_reason=fraud_details if not is_valid_location else ''
    )

    
    
    if lat_f and lng_f:
        import threading
        def _geocode(punch_id, lat, lng):
            try:
                import django
                from geopy.geocoders import Nominatim
                from attendance.models import AttendancePunch as _Punch
                geolocator = Nominatim(user_agent="app_local_hr")
                loc_data = geolocator.reverse((lat, lng), timeout=5, exactly_one=True)
                if loc_data:
                    _Punch.objects.filter(pk=punch_id).update(location_address=loc_data.address)
            except Exception:
                pass  
        t = threading.Thread(target=_geocode, args=(punch.pk, lat_f, lng_f), daemon=True)
        t.start()

    from core.audit import log_action
    label = 'Entrada' if next_action_type == 'IN' else 'Saída/Pausa'
    log_action(request, 'PUNCH', f'{user.username} registrou {label} em {local_now.strftime("%H:%M")}')
    messages.success(request, f'Sucesso! {label} registrada às {local_now.strftime("%H:%M")}')

    # Invalida caches do navbar e do banco de horas para refletir o novo estado
    from django.core.cache import cache as _cache
    _cache.delete(f'punch_ctx_{emp.pk}_{local_date}')
    _cache.delete(f'timebank_{emp.pk}_{local_date.year}_{local_date.month}')

    return redirect(request.META.get('HTTP_REFERER') or 'dashboard')
        
    now = timezone.now()
    local_now = timezone.localtime(now)   
    local_date = local_now.date()         
    
    
    from .models import get_work_info_for_date
    work_info = get_work_info_for_date(emp, local_date)
    if work_info.get('source') == 'leave' and not work_info.get('is_work_day'):
        messages.error(request, 'Ação bloqueada: Você está de licença no dia de hoje.')
        return redirect(request.META.get('HTTP_REFERER') or 'attendance_my')

    note = request.POST.get('note', '').strip()[:300]
    
    
    lat = request.POST.get('lat')
    lng = request.POST.get('lng')
    from ipware import get_client_ip
    from geopy.distance import geodesic
    
    client_ip, is_routable = get_client_ip(request)
    
    is_valid_location = False
    fraud_details = f"IP detectado: {client_ip}. Coordenadas detectadas: {lat}, {lng}. Locais associados ao funcionário não conferem."
    
    locations = emp.locations.all()
    if not locations.exists():
        
        is_valid_location = True
        fraud_details = None
    else:
        for loc in locations:
            
            if loc.allowed_ipv4 and client_ip and client_ip == loc.allowed_ipv4.strip():
                is_valid_location = True
                fraud_details = None
                break
                
            
            if not is_valid_location and lat and lng and loc.latitude and loc.longitude and loc.radius_meters:
                try:
                    user_coord = (float(lat), float(lng))
                    loc_coord = (loc.latitude, loc.longitude)
                    dist = geodesic(user_coord, loc_coord).meters
                    
                    if dist <= loc.radius_meters:
                        is_valid_location = True
                        fraud_details = None
                        break
                    else:
                        fraud_details = f"Tentativa falhou. Distância calculada até '{loc.name}': {dist:.2f}m (Raio permitido: {loc.radius_meters}m). IP: {client_ip}."
                except Exception as e:
                    fraud_details = f"Erro ao calcular distâncias geográficas do GPS: {str(e)}"
    
    
    photo_b64 = request.POST.get('photo_base64', '')
    photo_file = None
    if photo_b64:
        import base64
        import uuid
        from django.core.files.base import ContentFile
        try:
            format_str, imgstr = photo_b64.split(';base64,')
            ext = format_str.split('/')[-1].lower().strip()
            ALLOWED_PHOTO_EXTENSIONS = ['jpeg', 'jpg', 'png', 'webp']
            if ext not in ALLOWED_PHOTO_EXTENSIONS:
                ext = 'jpg'  
            photo_file = ContentFile(base64.b64decode(imgstr), name=f"{emp.id}_punch_{uuid.uuid4().hex[:8]}.{ext}")
        except Exception:
            pass

    
    existing_pending_today = PendingPunchRequest.objects.filter(
        employee=emp,
        status=PendingPunchRequest.STATUS_PENDING,
        requested_at__date=local_date,
    ).exists()

    action_type = request.POST.get('punch_action_type', '')
    record_today = AttendanceRecord.objects.filter(employee=emp, date=local_date).first()

    
    needs_photo = False
    if not record_today:
        needs_photo = True
        punch_action_label = 'Entrada'
    elif action_type == 'OUT':
        punch_action_label = 'Saída Final'
    elif record_today.state == AttendanceRecord.STATE_LUNCH_IN and not action_type:
        punch_action_label = 'Saída Final'
    else:
        punch_action_label = 'Pausa'

    
    if request.user and getattr(request.user, 'role', None):
        from core.models import RoleModuleAccess
        acc = RoleModuleAccess.objects.filter(role=request.user.role).first()
        if acc and getattr(acc, 'attendance_photo_all_punches', False):
            needs_photo = True

    is_invalid = (needs_photo and not photo_file) or not is_valid_location
    try:
        lat_f = float(lat) if lat else None
        lng_f = float(lng) if lng else None
    except (TypeError, ValueError):
        lat_f = lng_f = None

    
    msg = ""
    if not record_today:
        record_today = AttendanceRecord.objects.create(
            employee=emp, date=local_date,
            punch_in_utc_time=now, punch_in_user_time=now, punch_in_note=note,
            punch_in_photo=photo_file,
            state=AttendanceRecord.STATE_PUNCHED_IN,
            is_flagged_location=not is_valid_location,
            fraud_reason=fraud_details if not is_valid_location else '',
        )
        msg = f'Entrada registrada às {local_now.strftime("%H:%M")}!'
    else:
        record = record_today
        if not is_valid_location:
            record.is_flagged_location = True
            record.fraud_reason = (record.fraud_reason + ' | ' if record.fraud_reason else '') + fraud_details

        if record.state == AttendanceRecord.STATE_PUNCHED_IN:
            if action_type == 'OUT':
                record.punch_out_utc_time = now
                record.punch_out_user_time = now
                record.punch_out_note = note
                if photo_file:
                    record.punch_out_photo = photo_file
                record.state = AttendanceRecord.STATE_PUNCHED_OUT
                msg = f'Saída Final registrada às {local_now.strftime("%H:%M")}!'
            else:
                record.punch_lunch_out_utc_time = now
                record.punch_lunch_out_user_time = now
                record.punch_lunch_out_note = note
                record.state = AttendanceRecord.STATE_LUNCH_OUT
                msg = f'Saída para Almoço registrada às {local_now.strftime("%H:%M")}!'
        elif record.state == AttendanceRecord.STATE_LUNCH_OUT:
            record.punch_lunch_in_utc_time = now
            record.punch_lunch_in_user_time = now
            record.punch_lunch_in_note = note
            record.state = AttendanceRecord.STATE_LUNCH_IN
            msg = f'Retorno do Almoço registrado às {local_now.strftime("%H:%M")}!'
        elif record.state == AttendanceRecord.STATE_LUNCH_IN:
            record.punch_out_utc_time = now
            record.punch_out_user_time = now
            record.punch_out_note = note
            if photo_file:
                record.punch_out_photo = photo_file
            record.state = AttendanceRecord.STATE_PUNCHED_OUT
            msg = f'Saída Final registrada às {local_now.strftime("%H:%M")}!'
        else:
            messages.warning(request, 'Sua jornada diária já foi encerrada.')
            return redirect(request.META.get('HTTP_REFERER') or 'attendance_my')
            
        record.save()

    
    if is_invalid:
        reasons = []
        if needs_photo and not photo_file:
            reasons.append('foto não capturada')
        if not is_valid_location:
            reasons.append('localização não validada (fraude de GPS / IP)')
            
        fail_reason = f"Pendência de Auditoria: {', '.join(reasons)}. IP: {client_ip}. Coords: {lat},{lng}."
        
        pending_action = (
            PendingPunchRequest.ACTION_OUT
            if action_type == 'OUT' or (record_today.state == AttendanceRecord.STATE_PUNCHED_OUT)
            else PendingPunchRequest.ACTION_IN
        )

        PendingPunchRequest.objects.create(
            employee=emp,
            action_type=pending_action,
            requested_at=now,
            photo=photo_file,
            lat=lat_f,
            lng=lng_f,
            fail_reason=fail_reason,
            linked_record=record_today
        )

        messages.warning(request, f'⚠️ A sua {punch_action_label} foi registrada, mas foi <strong>enviada para análise do supervisor</strong> pois a {reasons[0]}.')
    else:
        messages.success(request, msg)

    next_url = request.META.get('HTTP_REFERER') or 'attendance_my'
    return redirect(next_url)







@login_required
def pending_punch_list(request):
    """Lista de batidas pendentes de aprovação para supervisores."""
    if not (request.user.is_supervisor() or request.user.is_admin()):
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')

    visible_emps = get_visible_employees(request.user)
    pending = PendingPunchRequest.objects.filter(
        employee__in=visible_emps,
        status=PendingPunchRequest.STATUS_PENDING,
    ).select_related('employee').order_by('-requested_at')

    return render(request, 'attendance/pending_punch_list.html', {'pending_list': pending})


@login_required
def pending_punch_approve(request, pk):
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from django.utils import timezone
    from .models import PendingPunchRequest, AttendancePunch
    if not (request.user.is_admin() or request.user.is_supervisor()):
        return redirect('dashboard')
        
    p_req = get_object_or_404(PendingPunchRequest, pk=pk)
    if p_req.status == PendingPunchRequest.STATUS_PENDING:
        from django.utils import timezone
        
        AttendancePunch.objects.create(
            attendance_record=p_req.linked_record,
            punch_type=p_req.action_type,
            timestamp_utc=p_req.requested_at,
            timestamp_user=timezone.localtime(p_req.requested_at),
            is_flagged_location=True,
            fraud_reason=p_req.fail_reason,
            photo=p_req.photo
        )
        
        p_req.status = PendingPunchRequest.STATUS_APPROVED
        p_req.reviewed_by = request.user
        p_req.reviewed_at = timezone.now()
        p_req.save()
        messages.success(request, 'Batida aprovada com sucesso!')
        # Invalida o cache do funcionário para atualizar o navbar
        from django.core.cache import cache as _cache
        _cache.delete(f'punch_ctx_{p_req.employee_id}_{p_req.linked_record.date}')
    return redirect(request.META.get('HTTP_REFERER', 'pending_punch_list'))



@login_required
def pending_punch_reject(request, pk):
    """Rejeita uma batida pendente — registro descartado."""
    if not (request.user.is_supervisor() or request.user.is_admin()):
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')

    pending = get_object_or_404(PendingPunchRequest, pk=pk, status=PendingPunchRequest.STATUS_PENDING)
    pending.status = PendingPunchRequest.STATUS_REJECTED
    pending.reviewed_by = request.user
    pending.reviewed_at = timezone.now()
    pending.save()

    messages.warning(request, f'Batida de {pending.employee.full_name} ({pending.get_action_type_display()}) rejeitada.')
    return redirect(request.META.get('HTTP_REFERER', 'pending_punch_list'))


@login_required
def punch_status_json(request):
    """Retorna o estado atual de ponto do dia como JSON — usado pelo polling da página web."""
    from django.http import JsonResponse
    from django.utils import timezone
    from .models import AttendanceRecord

    emp = getattr(request.user, 'employee', None)
    if not emp:
        return JsonResponse({'error': 'no employee'}, status=400)

    today = timezone.localdate()
    record = AttendanceRecord.objects.filter(employee=emp, date=today).first()

    current_state = None
    total_punches = 0
    net_hours = '0h 00m'
    punches = []

    if record:
        current_state = record.current_state   
        total_punches = record.punches.count()
        net_hours = record.net_hours_worked
        for p in record.punches.order_by('timestamp_utc'):
            punches.append({
                'type': p.punch_type,
                'time': p.timestamp_user.strftime('%H:%M'),
            })

    return JsonResponse({
        'current_state': current_state,
        'total_punches': total_punches,
        'net_hours': net_hours,
        'punches': punches,
    })


@login_required
@require_module('attendance')
def attendance_my(request):
    from django.shortcuts import redirect, render
    from django.contrib import messages
    from django.utils import timezone
    from .models import AttendanceRecord, get_work_info_for_date

    user = request.user
    emp = getattr(user, 'employee', None)
    if not emp:
        messages.error(request, 'Sua conta não tem um funcionário cadastrado.')
        return redirect('dashboard')
        
    now = timezone.now()
    local_now = timezone.localtime(now)
    local_date = local_now.date()
    
    records_qs = AttendanceRecord.objects.filter(employee=emp).prefetch_related('punches').order_by('-date')[:15]
    records = list(records_qs)
    
    if records:
        from .models import get_work_info_for_date_range
        start_d = min(r.date for r in records)
        end_d = max(r.date for r in records)
        bulk_info = get_work_info_for_date_range(emp, start_d, end_d)
        for r in records:
            r._prefetched_work_info = bulk_info.get(r.date, {})
    record_today = AttendanceRecord.objects.filter(employee=emp, date=local_date).first()
    
    work_info = get_work_info_for_date(emp, local_date)
    is_work_day = work_info.get('is_work_day', False)
    
    
    current_state = record_today.current_state if record_today else None
    
    if current_state == 'IN':
        next_action = 'OUT'
        button_color = 'danger'
        button_text = 'Pausar (Saída)'
    else:
        next_action = 'IN'
        button_color = 'primary'
        button_text = 'Iniciar (Entrada)'

    colleagues = []
    swap_requests = []
    pending_action_requests = []
    if emp and getattr(emp, 'sub_division', None):
        from pim.models import Employee
        colleagues = Employee.objects.filter(sub_division=emp.sub_division, state=Employee.STATE_ACTIVE).exclude(id=emp.id)
        from .models import ShiftSwapRequest
        pending_action_requests = ShiftSwapRequest.objects.filter(target_employee=emp, status='PENDING_TARGET').select_related('requester')

    require_photo_all = False
    if request.user and getattr(request.user, 'role', None):
        from django.core.cache import cache as _cache
        _cache_key = f'module_perms_{request.user.pk}_{request.user.role}'
        _acc_data = _cache.get(_cache_key)
        if _acc_data is not None:
            require_photo_all = _acc_data.get('attendance_photo_all_punches', False)
        else:
            from core.models import RoleModuleAccess
            acc = RoleModuleAccess.objects.filter(role=request.user.role).first()
            if acc:
                require_photo_all = getattr(acc, 'attendance_photo_all_punches', False)

    from django.core.signing import Signer
    from django.urls import reverse
    signer = Signer()
    signed_token = signer.sign(str(emp.id))
    import time
    feed_url = request.build_absolute_uri(
        reverse('roster_calendar_feed', kwargs={'signed_token': signed_token})
    ) + f"?t={int(time.time())}"

    return render(request, 'attendance/my_attendance.html', {
        'records': records,
        'record_today': record_today,
        'work_info': work_info,
        'next_action': next_action,
        'button_color': button_color,
        'button_text': button_text,
        'colleagues': colleagues,
        'swap_requests': swap_requests,
        'pending_action_requests': pending_action_requests,
        'require_photo_all_punches': require_photo_all,
        'feed_url': feed_url,
    })




@login_required
@require_module('attendance')
def attendance_my_calendar(request):
    import calendar
    from datetime import date, timedelta
    from django.utils import timezone
    from django.db import models
    from attendance.models import AttendanceRecord, get_work_info_for_date
    from leave.models import Leave, Holiday
    
    user = request.user
    emp = getattr(user, 'employee', None)
    if not emp:
        from django.contrib import messages
        messages.error(request, 'Usuário não tem funcionário associado.')
        from django.shortcuts import redirect
        return redirect('dashboard')
        
    try:
        year = int(request.GET.get('year', timezone.now().year))
        month = int(request.GET.get('month', timezone.now().month))
    except ValueError:
        year = timezone.now().year
        month = timezone.now().month
        
    
    cal = calendar.Calendar(firstweekday=0) 
    month_days = cal.monthdatescalendar(year, month)
    
    
    month_theo = 0
    month_actual = 0
    weeks_data = []
    
    today = timezone.now().date()
    
    
    target_week_start = today - timedelta(days=today.weekday())
    week_theo = 0
    week_actual = 0
    
    from datetime import date as dt_date
    import calendar as _cal
    from attendance.models import get_work_info_for_date_range

    # Coleta todas as datas do calendário do mês (incluindo dias de outros meses mostrados)
    all_dates_in_view = [d for week in month_days for d in week]
    start_of_view = min(all_dates_in_view)
    end_of_view = max(all_dates_in_view)
    
    # Bulk fetch de work_info para todo o mês com 5 queries no total
    month_work_info = get_work_info_for_date_range(emp, start_of_view, end_of_view)

    # Bulk fetch de registros de ponto do período (1 query)
    records_in_month = {
        r.date: r
        for r in AttendanceRecord.objects
            .filter(employee=emp, date__range=[start_of_view, end_of_view])
            .prefetch_related('punches')
    }
    # Injeta o work_info nos registros
    for d, r in records_in_month.items():
        r._prefetched_work_info = month_work_info.get(d, {})

    for week in month_days:
        week_days = []
        is_target_week = (target_week_start in week) if (year == today.year and month == today.month) else (week == month_days[0])
        
        for d in week:
            is_current_month = d.month == month
            info = month_work_info.get(d, {'is_work_day': False, 'theo_minutes': 0, 'source': 'default', 'entry_time': None, 'exit_time': None})
            
            
            actual_min = 0
            if d <= today:
                record = records_in_month.get(d)
                if record:
                    actual_min = record.net_minutes_worked
                    
                    if is_current_month:
                        month_actual += actual_min
                    if is_target_week:
                        week_actual += actual_min
                        
            
            if is_current_month:
                month_theo += info.get('theo_minutes', 0)
            if is_target_week:
                week_theo += info.get('theo_minutes', 0)
                
            day_status = 'normal'
            day_title = ''
            day_text = ''
            
            if info['source'] == 'holiday':
                day_status = 'feriado'
                # Reutiliza dados j\u00e1 carregados no work_info (sem query extra)
                day_title = info.get('title', 'Feriado')
                day_text = 'Dia Inteiro' if info['theo_minutes'] == 0 else 'Meio Per\u00edodo'
            elif info['source'] == 'leave':
                day_status = 'ausencia'
                # Reutiliza dados já carregados no work_info (sem query extra)
                leave_title = info.get('title', 'Licença')
                day_title = leave_title + (' (Pendente)' if False else '')
                if info.get('theo_minutes', 0) > 0:
                    day_status = 'ausencia-half'
            else:
                if info['is_work_day']:
                    day_status = 'trabalho'
                    if info['source'] == 'shift_override':
                        day_title = 'Escala (Roster)'
                    elif getattr(emp, 'work_schedule', None):
                        day_title = emp.work_schedule.name
                    else:
                        day_title = 'Jornada Padrão' if info['source'] == 'default' else 'Escala'
                        
                    if info['entry_time'] and info['exit_time']:
                        day_text = f"{info['entry_time'].strftime('%H:%M')} - {info['exit_time'].strftime('%H:%M')}"
                        
                        if info['source'] == 'work_schedule' and emp.work_schedule:
                            day_obj = emp.work_schedule.days.filter(weekday=d.weekday()).first()
                            if day_obj and day_obj.lunch_start and day_obj.lunch_end:
                                day_text = f"{info['entry_time'].strftime('%H:%M')} - {day_obj.lunch_start.strftime('%H:%M')} <br> {day_obj.lunch_end.strftime('%H:%M')} - {info['exit_time'].strftime('%H:%M')}"
                else:
                    day_status = 'folga'
                    day_title = 'Folga'
            
            week_days.append({
                'date': d,
                'day': d.day,
                'is_current_month': is_current_month,
                'is_today': d == today,
                'status': day_status,
                'title': day_title,
                'text': day_text,
                'theo_minutes': info.get('theo_minutes', 0),
                'actual_minutes': actual_min
            })
        weeks_data.append(week_days)
        
    def format_hm(mins):
        h = int(mins // 60)
        m = int(mins % 60)
        return f"{h}h {m:02d}min"
        
    
    month_names = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    month_names_short = ['', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    
    month_name = month_names[month]
    
    
    wk_s = month_days[0][0] if not (year == today.year and month == today.month) else target_week_start
    wk_e = wk_s + timedelta(days=6)
    week_str = f"{wk_s.day} de {month_names_short[wk_s.month]} - {wk_e.day} de {month_names_short[wk_e.month]}"
    
    
    if month == 1:
        prev_m = 12
        prev_y = year - 1
    else:
        prev_m = month - 1
        prev_y = year
        
    if month == 12:
        next_m = 1
        next_y = year + 1
    else:
        next_m = month + 1
        next_y = year

    
    month_progress = 0
    if month_theo > 0:
        month_progress = min(100, int((month_actual / month_theo) * 100))
        
    week_progress = 0
    if week_theo > 0:
        week_progress = min(100, int((week_actual / week_theo) * 100))

    # Permitir navegação irrestrita para visualização de escalas e folgas futuras no calendário
    allow_next_month = True

    from django.core.signing import Signer
    from django.urls import reverse
    signer = Signer()
    signed_token = signer.sign(str(emp.id))
    import time
    feed_url = request.build_absolute_uri(
        reverse('roster_calendar_feed', kwargs={'signed_token': signed_token})
    ) + f"?t={int(time.time())}"

    context = {
        'weeks': weeks_data,
        'year': year,
        'month': month,
        'month_name': month_name,
        'week_str': week_str,
        'prev_year': prev_y,
        'prev_month': prev_m,
        'next_year': next_y,
        'next_month': next_m,
        'allow_next_month': allow_next_month,
        'month_actual_str': format_hm(month_actual),
        'month_theo_str': format_hm(month_theo),
        'month_progress': month_progress,
        'week_actual_str': format_hm(week_actual),
        'week_theo_str': format_hm(week_theo),
        'week_progress': week_progress,
        'feed_url': feed_url,
    }
    from core.models import GoogleIntegration
    context['google_integration'] = GoogleIntegration.objects.filter(user=request.user).first()

    from django.shortcuts import render
    return render(request, 'attendance/my_calendar.html', context)



@login_required
def schedule_list(request):
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')
    schedules = WorkSchedule.objects.all()
    return render(request, 'attendance/schedule_list.html', {'schedules': schedules})


@login_required
def schedule_create(request):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        messages.error(request, 'Acesso Restrito')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = WorkScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save()
            for i in range(7):
                is_work = request.POST.get(f'is_work_{i}') == 'on'
                entry = request.POST.get(f'entry_{i}') or None
                exit_t = request.POST.get(f'exit_{i}') or None
                l_start = request.POST.get(f'lunch_start_{i}') or None
                l_end = request.POST.get(f'lunch_end_{i}') or None
                
                WorkScheduleDay.objects.create(
                    schedule=schedule, weekday=i, is_work_day=is_work,
                    entry_time=entry if is_work else None,
                    exit_time=exit_t if is_work else None,
                    lunch_start=l_start if is_work else None,
                    lunch_end=l_end if is_work else None
                )
            messages.success(request, f'Escala "{schedule.name}" criada!')
            return redirect('schedule_list')
    else:
        form = WorkScheduleForm()
        
    days_data = [{'weekday': i, 'name': WEEKDAY_CHOICES[i][1], 'is_work_day': i<5} for i in range(7)]
    return render(request, 'attendance/schedule_form.html', {'form': form, 'title': 'Nova Escala', 'days_data': days_data})


@login_required
def schedule_edit(request, pk):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        messages.error(request, 'Acesso Restrito')
        return redirect('dashboard')
        
    schedule = get_object_or_404(WorkSchedule, pk=pk)
    
    if request.method == 'POST':
        form = WorkScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            for i in range(7):
                day_obj = schedule.days.filter(weekday=i).first()
                if not day_obj:
                    day_obj = WorkScheduleDay(schedule=schedule, weekday=i)
                    
                is_work = request.POST.get(f'is_work_{i}') == 'on'
                day_obj.is_work_day = is_work
                day_obj.entry_time = request.POST.get(f'entry_{i}') or None if is_work else None
                day_obj.exit_time = request.POST.get(f'exit_{i}') or None if is_work else None
                day_obj.lunch_start = request.POST.get(f'lunch_start_{i}') or None if is_work else None
                day_obj.lunch_end = request.POST.get(f'lunch_end_{i}') or None if is_work else None
                day_obj.save()
            messages.success(request, f'Escala "{schedule.name}" atualizada!')
            return redirect('schedule_list')
    else:
        form = WorkScheduleForm(instance=schedule)
        
    days_data = []
    for i in range(7):
        day_obj = schedule.days.filter(weekday=i).first()
        days_data.append({
            'weekday': i, 'name': WEEKDAY_CHOICES[i][1],
            'is_work_day': day_obj.is_work_day if day_obj else (i<5),
            'entry_time': f"{day_obj.entry_time.strftime('%H:%M')}" if (day_obj and day_obj.entry_time) else '',
            'exit_time': f"{day_obj.exit_time.strftime('%H:%M')}" if (day_obj and day_obj.exit_time) else '',
            'lunch_start': f"{day_obj.lunch_start.strftime('%H:%M')}" if (day_obj and day_obj.lunch_start) else '',
            'lunch_end': f"{day_obj.lunch_end.strftime('%H:%M')}" if (day_obj and day_obj.lunch_end) else '',
        })
        
    return render(request, 'attendance/schedule_form.html', {'form': form, 'title': 'Editar Escala', 'schedule': schedule, 'days_data': days_data})


@login_required
def schedule_delete(request, pk):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('schedule_list')
    schedule = get_object_or_404(WorkSchedule, pk=pk)
    if request.method == 'POST':
        name = schedule.name
        schedule.delete()
        messages.success(request, f'Escala "{name}" removida.')
        return redirect('schedule_list')
    return render(request, 'attendance/schedule_confirm_delete.html', {'schedule': schedule})


@login_required
def assign_schedule(request, emp_pk):
    """Associar escala de trabalho a um funcionario especifico."""
    if not request.user.is_supervisor():
        messages.error(request, 'Acesso restrito.')
        return redirect('dashboard')
    employee = get_object_or_404(Employee, pk=emp_pk)
    schedules = WorkSchedule.objects.filter(is_active=True)
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        from .models import WorkScheduleAssignment
        import datetime
        from django.utils import timezone
        from django.utils.dateparse import parse_date
        
        
        start_date_str = request.POST.get('start_date')
        if start_date_str:
            target_start = parse_date(start_date_str) or timezone.now().date()
        else:
            target_start = timezone.now().date()
            
        yesterday_target = target_start - datetime.timedelta(days=1)
        
        
        WorkScheduleAssignment.objects.filter(employee=employee, start_date__gte=target_start).delete()
        
        
        open_assignments = WorkScheduleAssignment.objects.filter(employee=employee, end_date__isnull=True)
        
        if not open_assignments.exists() and employee.work_schedule:
            
            WorkScheduleAssignment.objects.create(
                employee=employee,
                schedule=employee.work_schedule,
                start_date=datetime.date(2000, 1, 1),
                end_date=yesterday_target
            )
            
        
        WorkScheduleAssignment.objects.filter(
            employee=employee,
            end_date__isnull=True
        ).update(end_date=yesterday_target)

        if schedule_id and schedule_id != 'none':
            new_schedule = get_object_or_404(WorkSchedule, pk=schedule_id)
            employee.work_schedule = new_schedule
            
            
            WorkScheduleAssignment.objects.create(
                employee=employee,
                schedule=new_schedule,
                start_date=target_start
            )
        else:
            employee.work_schedule = None
            
        employee.save()
        messages.success(request, f'Escala atualizada para {employee.full_name}!')
        return redirect_with_popup(request, 'employee_detail', pk=emp_pk)
    return render(request, 'attendance/assign_schedule.html', {
        'employee': employee,
        'schedules': schedules,
        'current_schedule': employee.work_schedule,
    })


class AttendanceAdjustmentForm(forms.ModelForm):
    class Meta:
        model = AttendanceAdjustment
        fields = ['date', 'requested_punches', 'reason']
        widgets = {
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

@login_required
@require_module('attendance')
def adjustment_list(request):
    user = request.user
    if user.is_admin():
        adjustments = AttendanceAdjustment.objects.all().select_related('employee', 'reviewed_by').order_by('-created_at')
    elif user.is_supervisor():
        visible_emps = get_visible_employees(user)
        adjustments = AttendanceAdjustment.objects.filter(employee__in=visible_emps).select_related('employee', 'reviewed_by').order_by('-created_at')
    else:
        emp = getattr(user, 'employee', None)
        if emp:
            adjustments = AttendanceAdjustment.objects.filter(employee=emp).select_related('employee', 'reviewed_by').order_by('-created_at')
        else:
            adjustments = []
    return render(request, 'attendance/adjustment_list.html', {'adjustments': adjustments})

@login_required
@require_module('attendance')
def adjustment_create(request):
    emp = getattr(request.user, 'employee', None)
    if not emp:
        messages.error(request, 'Usuário não vinculado a funcionário.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AttendanceAdjustmentForm(request.POST)
        if form.is_valid():
            adj = form.save(commit=False)
            adj.employee = emp
            record = AttendanceRecord.objects.filter(employee=emp, date=adj.date).first()
            if record:
                adj.attendance_record = record
            adj.save()
            messages.success(request, 'Solicitação enviada com sucesso!')
            return redirect('adjustment_list')
    else:
        from django.utils import timezone
        form = AttendanceAdjustmentForm(initial={'date': timezone.now().date()})
    return render(request, 'attendance/adjustment_form.html', {'form': form, 'title': 'Solicitar Ajuste de Ponto'})

@login_required
def adjustment_approve(request, pk):
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from .models import AttendanceAdjustment, AttendanceRecord, AttendancePunch
    if not (request.user.is_admin() or request.user.is_supervisor()):
        return redirect('dashboard')
        
    adj = get_object_or_404(AttendanceAdjustment, pk=pk)
    user = request.user
    my_employee = getattr(user, 'employee', None)
    
    is_direct_supervisor = False
    if my_employee:
        is_direct_supervisor = adj.employee.supervisors.filter(pk=my_employee.pk).exists()
        if not is_direct_supervisor and my_employee.sub_division and adj.employee.sub_division == my_employee.sub_division:
            is_direct_supervisor = True

    if adj.status == AttendanceAdjustment.STATUS_PENDING:
        if is_direct_supervisor or user.role == 'Admin':
            adj.status = AttendanceAdjustment.STATUS_SUPERVISOR_APPROVED
            adj.reviewed_at = timezone.now()
            adj.reviewed_by = user
            adj.save()
            messages.success(request, 'Ajuste pré-aprovado pelo Gestor! O RH será notificado para validação final.')
        else:
            messages.error(request, 'Apenas o gestor direto ou administrador pode pré-aprovar um ajuste pendente.')
            
    elif adj.status == AttendanceAdjustment.STATUS_SUPERVISOR_APPROVED:
        if user.is_hr() or user.is_admin():
            from datetime import datetime
            import pytz
            from django.utils import timezone
            tz = timezone.get_current_timezone()
            
            record, _ = AttendanceRecord.objects.get_or_create(
                employee=adj.employee, date=adj.date
            )
            
            AttendancePunch.objects.filter(attendance_record=record).delete()
            
            punches = adj.requested_punches
            if isinstance(punches, list):
                for idx, time_str in enumerate(punches):
                    try:
                        time_obj = datetime.strptime(time_str, '%H:%M').time()
                        dt_loc = datetime.combine(adj.date, time_obj)
                        dt_loc_aware = timezone.make_aware(dt_loc, tz)
                        dt_utc = dt_loc_aware.astimezone(pytz.UTC)
                        
                        p_type = 'IN' if idx % 2 == 0 else 'OUT'
                        
                        AttendancePunch.objects.create(
                            attendance_record=record,
                            punch_type=p_type,
                            timestamp_utc=dt_utc,
                            timestamp_user=dt_loc_aware
                        )
                    except Exception:
                        pass
                
            adj.attendance_record = record
            adj.status = AttendanceAdjustment.STATUS_APPROVED
            adj.reviewed_at = timezone.now()
            adj.reviewed_by = user
            adj.save()
            messages.success(request, 'Ajuste aprovado definitivamente pelo RH! Ponto atualizado.')
        else:
            messages.error(request, 'Apenas o RH ou administrador pode realizar a aprovação final.')
            
    return redirect('adjustment_list')


@login_required
def adjustment_reject(request, pk):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        messages.error(request, 'Acesso Restrito')
        return redirect('dashboard')
        
    adj = get_object_or_404(AttendanceAdjustment, pk=pk)
    user = request.user
    my_employee = getattr(user, 'employee', None)
    
    is_direct_supervisor = False
    if my_employee:
        is_direct_supervisor = adj.employee.supervisors.filter(pk=my_employee.pk).exists()
        if not is_direct_supervisor and my_employee.sub_division and adj.employee.sub_division == my_employee.sub_division:
            is_direct_supervisor = True

    if user.is_hr() or user.is_admin():
        if adj.status in [AttendanceAdjustment.STATUS_PENDING, AttendanceAdjustment.STATUS_SUPERVISOR_APPROVED]:
            adj.status = AttendanceAdjustment.STATUS_REJECTED
            adj.reviewed_by = user
            adj.save()
            from core.audit import log_action
            log_action(request, 'ADJ_REJECT',
                f'{user.username} (RH/Admin) rejeitou ajuste de ponto de {adj.employee.full_name} '
                f'em {adj.date.strftime("%d/%m/%Y")}.')
            messages.warning(request, 'Ajuste rejeitado pelo RH!')
        else:
            messages.error(request, 'Este ajuste não pode ser rejeitado no estágio atual.')
            
    elif is_direct_supervisor:
        if adj.status == AttendanceAdjustment.STATUS_PENDING:
            adj.status = AttendanceAdjustment.STATUS_REJECTED
            adj.reviewed_by = user
            adj.save()
            from core.audit import log_action
            log_action(request, 'ADJ_REJECT',
                f'{user.username} (Gestor) rejeitou ajuste de ponto de {adj.employee.full_name} '
                f'em {adj.date.strftime("%d/%m/%Y")}.')
            messages.warning(request, 'Ajuste rejeitado pelo Gestor!')
        else:
            messages.error(request, 'Você só pode rejeitar ajustes pendentes.')
    else:
        messages.error(request, 'Você não tem permissão para rejeitar este ajuste.')
        
    return redirect('adjustment_list')


@login_required
def admin_reports(request):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        messages.error(request, 'Acesso Restrito')
        return redirect('dashboard')
        
    now = timezone.now()
    today = now.date()
    
    
    department_id = request.GET.get('department', '')
    if department_id == 'all': department_id = ''
    employee_id = request.GET.get('employee', '')
    if employee_id == 'all': employee_id = ''
    month_filter = request.GET.get('month', str(now.month))
    year_filter = request.GET.get('year', str(now.year))
    
    try:
        month_filter = int(month_filter)
        year_filter = int(year_filter)
    except:
        month_filter = now.month
        year_filter = now.year
    
    visible_employees = get_visible_employees(request.user)
    
    emp_dict = {e.id: e for e in visible_employees}
    
    
    records_query = AttendanceRecord.objects.filter(
        date__year=year_filter,
        date__month=month_filter,
        employee__in=visible_employees
    ).select_related('employee', 'employee__sub_division').prefetch_related('punches').order_by('employee_id', 'date')
    
    if department_id:
        records_query = records_query.filter(employee__sub_division_id=department_id)
    if employee_id:
        records_query = records_query.filter(employee_id=employee_id)
        
    from leave.models import Leave
    approved_leaves = Leave.objects.filter(
        employee__in=visible_employees,
        date__year=year_filter,
        date__month=month_filter,
        status='APPROVED'
    ).select_related('leave_type')
    leaves_dict = {(l.employee_id, l.date): l for l in approved_leaves}

    emp_stats = {}
    dept_lates = {}
    
    
    interjornada_risks = []
    intrajornada_risks = []
    burnout_risks = []
    
    
    todays_records = set()
    last_record_per_emp = {}
    
    records_list = list(records_query)
    
    from attendance.models import get_work_info_for_date_bulk
    unique_dates = set(r.date for r in records_list)
    emps_in_records = list(set(r.employee for r in records_list))
    
    bulk_work_info_by_date = {}
    for d in unique_dates:
        bulk_work_info_by_date[d] = get_work_info_for_date_bulk(emps_in_records, d)
        
    for r in records_list:
        r.leave_info = leaves_dict.get((r.employee_id, r.date))
        r._prefetched_work_info = bulk_work_info_by_date.get(r.date, {}).get(r.employee_id, {})
        emp = r.employee
        emp_name = emp.full_name
        dept_name = emp.sub_division.name if emp.sub_division else 'Sem Setor'
        
        if r.date == today:
            todays_records.add(emp.id)
            
        if emp_name not in emp_stats:
            emp_stats[emp_name] = {'minutes': 0, 'extra_minutes': 0, 'lates': 0, 'avatar': '', 'dept': dept_name, 'points': 0}
            if hasattr(emp, 'picture') and emp.picture and emp.picture.picture:
                emp_stats[emp_name]['avatar'] = emp.picture.picture.url
                
        emp_stats[emp_name]['minutes'] += float(r.net_minutes_worked)
        if hasattr(r, 'dailytimebalance'):
            emp_stats[emp_name]['extra_minutes'] += (r.dailytimebalance.extra_60_minutes + r.dailytimebalance.extra_100_minutes)
        emp_stats[emp_name]['points'] += 1 
        
        if r.is_late:
            emp_stats[emp_name]['lates'] += 1
            if dept_name not in dept_lates: dept_lates[dept_name] = 0
            dept_lates[dept_name] += 1
            
        
        punches = sorted(list(r.punches.all()), key=lambda p: p.timestamp_user)
        if not punches: continue
        
        
        if r.net_minutes_worked > 600:
            burnout_risks.append({
                'name': emp_name, 
                'dept': dept_name,
                'date': r.date.strftime('%d/%m/%Y'),
                'hours': round(r.net_minutes_worked/60.0, 1),
                'avatar': emp_stats[emp_name]['avatar']
            })
            
        
        in_punches = [p for p in punches if p.punch_type == 'IN']
        out_punches = [p for p in punches if p.punch_type == 'OUT']
        
        if len(out_punches) >= 1 and len(in_punches) >= 2:
            try:
                lunch_duration = (in_punches[1].timestamp_user - out_punches[0].timestamp_user).total_seconds() / 60.0
                if 5 < lunch_duration < 55:
                    intrajornada_risks.append({
                        'name': emp_name, 'date': r.date.strftime('%d/%m/%Y'), 'lunch_minutes': int(lunch_duration)
                    })
            except Exception:
                pass
                
        
        first_in = in_punches[0] if in_punches else None
        last_out = out_punches[-1] if out_punches else None
        
        prev_out = last_record_per_emp.get(emp.id)
        if first_in and prev_out:
            rest_duration = (first_in.timestamp_user.replace(tzinfo=None) - prev_out.replace(tzinfo=None)).total_seconds() / 3600.0
            if 1 < rest_duration < 10.8:
                interjornada_risks.append({
                    'name': emp_name, 'date': r.date.strftime('%d/%m/%Y'), 'rest_hours': round(rest_duration, 1)
                })
                
        if last_out:
            last_record_per_emp[emp.id] = last_out.timestamp_user
            
    
    missing_today = []
    if year_filter == now.year and month_filter == now.month:
        if department_id:
            emps_to_check = [e for e in emp_dict.values() if str(e.sub_division_id) == str(department_id)]
        else:
            emps_to_check = list(emp_dict.values())
            
        today_bulk_work_info = bulk_work_info_by_date.get(today)
        if not today_bulk_work_info:
            today_bulk_work_info = get_work_info_for_date_bulk(emps_to_check, today)
            
        for emp in emps_to_check:
            if emp.id not in todays_records:
                work_info = today_bulk_work_info.get(emp.id, {})
                
                if work_info.get('is_work_day') and work_info.get('entry_time'):
                    import datetime
                    entry_dt = datetime.datetime.combine(today, work_info['entry_time'])
                    if now.replace(tzinfo=None) > entry_dt:
                        missing_today.append({
                            'name': emp.full_name,
                            'dept': emp.sub_division.name if emp.sub_division else 'Sem Setor',
                            'avatar': emp.picture.picture.url if (hasattr(emp, 'picture') and emp.picture and emp.picture.picture) else ''
                        })

    
    from .models import DailyTimeBalance
    dtbs = DailyTimeBalance.objects.filter(
        date__year=year_filter, date__month=month_filter,
        employee__in=visible_employees
    ).select_related('employee', 'employee__sub_division')
    
    if department_id:
        dtbs = dtbs.filter(employee__sub_division_id=department_id)
    if employee_id:
        dtbs = dtbs.filter(employee_id=employee_id)
        
    dept_costs = {}
    for dtb in dtbs:
        dept = dtb.employee.sub_division.name if dtb.employee.sub_division else 'Sem Setor'
        if dept not in dept_costs:
            dept_costs[dept] = {'he_50': 0, 'he_100': 0, 'night': 0}
            
        dept_costs[dept]['he_50'] += dtb.extra_60_minutes
        dept_costs[dept]['he_100'] += dtb.extra_100_minutes
        dept_costs[dept]['night'] += dtb.night_minutes

    
    import json
    
    sorted_emps = sorted(emp_stats.items(), key=lambda x: (-x[1]['lates'], -x[1]['minutes']))
    top_lates = [{'name': k, 'lates': v['lates'], 'avatar': v['avatar'], 'dept': v['dept']} for k,v in sorted_emps[:5] if v['lates'] > 0]
    
    sorted_punctual = sorted(emp_stats.items(), key=lambda x: (x[1]['lates'], -x[1]['points']))
    top_punctuals = [{'name': k, 'points': v['points'], 'avatar': v['avatar'], 'dept': v['dept']} for k,v in sorted_punctual[:5] if v['lates'] == 0 and v['points'] > 0]
    
    table_stats = []
    for emp_name, stats in sorted_emps:
        h = int(stats['minutes'] // 60)
        m = int(stats['minutes'] % 60)
        eh = int(stats.get('extra_minutes', 0) // 60)
        em = int(stats.get('extra_minutes', 0) % 60)
        table_stats.append({
            'name': emp_name,
            'dept': stats['dept'],
            'formatted_hours': f"{h}h {m:02d}m",
            'formatted_extra': f"{eh}h {em:02d}m" if stats.get('extra_minutes', 0) > 0 else "0h 00m",
            'lates': stats['lates'],
            'minutes': stats['minutes'],
            'avatar': stats['avatar']
        })
        
    from admin_app.models import Subunit
    from pim.models import Employee
    if request.user.is_admin():
        available_departments = Subunit.objects.all()
    else:
        my_emp = getattr(request.user, 'employee', None)
        if my_emp and my_emp.sub_division:
            available_departments = Subunit.objects.filter(pk=my_emp.sub_division.pk)
        else:
            available_departments = Subunit.objects.none()
            
    cost_labels = list(dept_costs.keys())
    he50 = [round(dept_costs[k]['he_50']/60.0, 1) for k in cost_labels]
    he100 = [round(dept_costs[k]['he_100']/60.0, 1) for k in cost_labels]
    night = [round(dept_costs[k]['night']/60.0, 1) for k in cost_labels]
    
    total_he_min = sum([d['he_50'] + d['he_100'] for d in dept_costs.values()])
    kpi_he = f"{int(total_he_min//60)}h {int(total_he_min%60):02d}m"
    kpi_lates = sum([d['lates'] for d in emp_stats.values()])
    
    from .models import PendingPunchRequest, AttendanceAdjustment
    kpi_pendings = PendingPunchRequest.objects.filter(status=PendingPunchRequest.STATUS_PENDING, employee__in=visible_employees).count()
    kpi_adjustments = AttendanceAdjustment.objects.filter(status=AttendanceAdjustment.STATUS_PENDING, employee__in=visible_employees).count()
    
    context = {
        'cost_labels': json.dumps(cost_labels),
        'cost_he50': json.dumps(he50),
        'cost_he100': json.dumps(he100),
        'cost_night': json.dumps(night),
        
        'dept_lates_labels': json.dumps(list(dept_lates.keys())),
        'dept_lates_data': json.dumps(list(dept_lates.values())),
        
        'top_lates': top_lates,
        'top_punctuals': top_punctuals,
        'missing_today': missing_today[:6],
        'burnout_risks': burnout_risks,
        
        'intrajornada_risks': intrajornada_risks,
        'interjornada_risks': interjornada_risks,
        
        'table_stats': table_stats,
        
        'kpi_he': kpi_he,
        'kpi_lates': kpi_lates,
        'kpi_pendings': kpi_pendings,
        'kpi_adjustments': kpi_adjustments,
        
        'month_name': f"{month_filter:02d}/{year_filter}",
        'selected_month': month_filter,
        'selected_year': year_filter,
        
        'departments': available_departments,
        'employees': visible_employees.filter(state=Employee.STATE_ACTIVE, **({'sub_division_id': department_id} if department_id else {})).order_by('first_name'),
        'selected_department': int(department_id) if department_id.isdigit() else '',
        'selected_employee': int(employee_id) if employee_id.isdigit() else '',
        
        'records': records_list,
    }
    return render(request, 'attendance/admin_reports.html', context)



@login_required
@require_module('attendance')
def attendance_stats(request):
    """Estatísticas pessoais de ponto — acessível a todos os funcionários."""
    from datetime import date, timedelta

    user = request.user
    emp  = getattr(user, 'employee', None)
    
    target_emp_id = request.GET.get('emp_id')
    if target_emp_id and getattr(user, 'role', '') == 'HR':
        from pim.models import Employee
        target_emp = Employee.objects.filter(pk=target_emp_id).first()
        if target_emp:
            emp = target_emp
            messages.info(request, f"Exibindo registros de {emp.full_name} para análise de contexto.")
            
    if not emp:
        messages.error(request, 'Usuário não vinculado a um funcionário.')
        return redirect('dashboard')

    import calendar
    today        = timezone.localtime(timezone.now()).date()
    default_from = today.replace(day=1)
    _, last_day  = calendar.monthrange(today.year, today.month)
    default_to   = today.replace(day=last_day)

    raw_from = request.GET.get('date_from', '')
    raw_to   = request.GET.get('date_to', '')

    try:
        date_from = date.fromisoformat(raw_from) if raw_from else default_from
    except ValueError:
        date_from = default_from

    try:
        date_to = date.fromisoformat(raw_to) if raw_to else default_to
    except ValueError:
        date_to = default_to

    if date_from > date_to:
        date_from, date_to = date_to, date_from

    from django.core.cache import cache
    cache_key = f'attendance_stats_{emp.id}_{date_from.year}_{date_from.month}'
    cached_stats = cache.get(cache_key)

    if True: 
        records = list(
            AttendanceRecord.objects.filter(employee=emp, date__gte=date_from, date__lte=date_to)
            .prefetch_related('punches')
            .order_by('date')
        )

        schedule = getattr(emp, 'work_schedule', None)

        
        work_days_set = set(schedule.work_days_list) if schedule else {0, 1, 2, 3, 4}

        
        from attendance.models import get_work_info_for_date_range
        _work_info_cache = get_work_info_for_date_range(emp, date_from, date_to)

        def cached_get_work_info(date_val):
            return _work_info_cache.get(date_val, {'is_work_day': False, 'theo_minutes': 0})

        def count_workdays(start, end):
            """Conta os dias de trabalho conforme o padrão/escala do funcionário."""
            total, cur = 0, start
            while cur <= end:
                info = cached_get_work_info(cur)
                if info['is_work_day']:
                    total += 1
                cur += timedelta(days=1)
            return total

        
        working_days_in_period = count_workdays(date_from, date_to)
        days_with_record       = len(records)

        
        effective_to      = min(date_to, today)
        past_working_days = count_workdays(date_from, effective_to) if date_from <= effective_to else 0
        absences          = max(0, past_working_days - days_with_record)

        def break_minutes(rec):
            punches = sorted(list(rec.punches.all()), key=lambda p: p.timestamp_user)
            b_mins = 0
            last_out = None
            for p in punches:
                if p.punch_type == 'OUT':
                    last_out = p.timestamp_utc
                elif p.punch_type == 'IN':
                    if last_out:
                        b_mins += (p.timestamp_utc - last_out).total_seconds() / 60
                        last_out = None
        
            if len(punches) <= 2:
                work_info = cached_get_work_info(rec.date)
                auto_break = work_info.get('automatic_break_minutes', 0)
                if auto_break > 0 and b_mins < auto_break:
                    
                    
                    b_mins += auto_break
                
            return max(0, b_mins)

        total_worked_min = sum(float(r.net_minutes_worked) for r in records)
        total_break_min  = sum(break_minutes(r) for r in records)

        theoretical_min = 0          
        month_theoretical_min = 0    
    
        cur_date = date_from
        while cur_date <= date_to:
            info = cached_get_work_info(cur_date)
            if cur_date <= today:
                theoretical_min += info['theo_minutes']
            month_theoretical_min += info['theo_minutes']
            cur_date += timedelta(days=1)

        balance_min = total_worked_min - theoretical_min
        completed = []
        for r in records:
            punches = sorted(list(r.punches.all()), key=lambda p: p.timestamp_user)
            if punches:
                first_in = next((p for p in punches if p.punch_type == 'IN'), None)
                last_out = next((p for p in reversed(punches) if p.punch_type == 'OUT'), None)
                if first_in and last_out:
                    completed.append({
                        'in': timezone.localtime(first_in.timestamp_user),
                        'out': timezone.localtime(last_out.timestamp_user)
                    })

        avg_entry = avg_exit = None
        if completed:
            avg_e = sum(p['in'].hour  * 60 + p['in'].minute  for p in completed) / len(completed)
            avg_x = sum(p['out'].hour * 60 + p['out'].minute for p in completed) / len(completed)
            avg_entry = f"{int(avg_e//60):02d}:{int(avg_e%60):02d}"
            avg_exit  = f"{int(avg_x//60):02d}:{int(avg_x%60):02d}"

        for r in records:
            r._prefetched_work_info = _work_info_cache.get(r.date, {})
        lates_count = sum(1 for r in records if r.is_late)

        def fmt_min(mins):
            sign = '-' if mins < 0 else ''
            m = abs(int(mins))
            return f"{sign}{m//60}h {m%60:02d}m"

        daily_rows = []
        records_by_date = {r.date: r for r in records}
    
        
        from django.db.models import Q
        from attendance.models import ShiftSwapRequest
        swaps_qs = ShiftSwapRequest.objects.filter(
            Q(requester=emp) | Q(target_employee=emp),
            date__range=[date_from, date_to],
            status='APPROVED'
        ).values_list('date', flat=True)
        swapped_dates = set(swaps_qs)
    
        
        from leave.models import Leave as _Leave, Holiday as _Holiday
        leaves_in_range = _Leave.objects.filter(
            employee=emp,
            date__range=[date_from, date_to]
        ).exclude(status__in=[_Leave.STATUS_REJECTED, _Leave.STATUS_CANCELLED])         .select_related('leave_request__leave_type')
        leaves_by_date = {l.date: l for l in leaves_in_range}

        holidays_in_range = _Holiday.objects.filter(
            date__range=[date_from, date_to]
        )
        if emp.city_id:
            from django.db.models import Q
            holidays_in_range = holidays_in_range.filter(Q(is_global=True) | Q(cities__id=emp.city_id))
        else:
            holidays_in_range = holidays_in_range.filter(is_global=True)

        holidays_by_date = {h.date: h for h in holidays_in_range}

        cur_date = date_from
        acc_bal = 0
        while cur_date <= date_to:
            r = records_by_date.get(cur_date)
            info = cached_get_work_info(cur_date)
            day_theo = info['theo_minutes']

            bars = []
            shifts = []
            entry_str = '—'
            exit_str = '—'
            entry_full_str = '—'
            exit_full_str = '—'
        
            if r:
                punches = sorted(list(r.punches.all()), key=lambda p: p.timestamp_user)
            
                first_in = next((p for p in punches if p.punch_type == 'IN'), None)
                last_out = next((p for p in reversed(punches) if p.punch_type == 'OUT'), None)
            
                if first_in:
                    loc_first = timezone.localtime(first_in.timestamp_user)
                    entry_str = loc_first.strftime('%H:%M')
                    entry_full_str = loc_first.strftime('%H:%M:%S')
                if last_out:
                    loc_last = timezone.localtime(last_out.timestamp_user)
                    exit_str = loc_last.strftime('%H:%M')
                    exit_full_str = loc_last.strftime('%H:%M:%S')
                
                for i in range(len(punches)):
                    if punches[i].punch_type == 'IN':
                        p_in = punches[i]
                        p_out = None
                        for j in range(i+1, len(punches)):
                            if punches[j].punch_type == 'OUT':
                                p_out = punches[j]
                                break
                            
                        if p_out:
                            loc_in = timezone.localtime(p_in.timestamp_user)
                            loc_out = timezone.localtime(p_out.timestamp_user)
                            in_mins = loc_in.hour * 60 + loc_in.minute
                            out_mins = loc_out.hour * 60 + loc_out.minute
                            width = out_mins - in_mins
                            if width > 0:
                                bars.append({
                                    'left': f"{(in_mins / 1440.0) * 100:.4f}",
                                    'width': f"{(width / 1440.0) * 100:.4f}",
                                    'start_fmt': loc_in.strftime('%H:%M'),
                                    'end_fmt': loc_out.strftime('%H:%M')
                                })
                                shifts.append({
                                    'start_full': loc_in.strftime('%H:%M:%S'),
                                    'end_full': loc_out.strftime('%H:%M:%S')
                                })

            day_worked_min = float(r.net_minutes_worked) if r else 0
        
            
            bal = 0
            if cur_date <= today:
                bal = day_worked_min - day_theo
                acc_bal += bal

            
            _day_source = info.get('source', 'default')
            leave_label = ''
            if _day_source == 'leave':
                _lv = leaves_by_date.get(cur_date)
                if _lv and _lv.leave_request and _lv.leave_request.leave_type:
                    leave_label = _lv.leave_request.leave_type.name
                    if _lv.status != _Leave.STATUS_APPROVED:
                        leave_label += ' (Pendente)'
                else:
                    leave_label = 'Licença'
            elif _day_source == 'holiday':
                _hol = holidays_by_date.get(cur_date)
                leave_label = _hol.name if _hol else 'Feriado'

            daily_rows.append({
                'date': cur_date,
                'is_weekend': cur_date.weekday() >= 5,
                'is_work_day': info['is_work_day'],
                'source': _day_source,
                'leave_label': leave_label,
                'entry': entry_str,
                'exit': exit_str,
                'entry_full': entry_full_str,
                'exit_full': exit_full_str,
                'worked_fmt': fmt_min(day_worked_min),
                'theo_fmt': fmt_min(day_theo),
                'balance': fmt_min(bal),
                'balance_neg': bal < 0,
                'acc_balance': fmt_min(acc_bal),
                'acc_balance_neg': acc_bal < 0,
                'is_late': r.is_late if r else False,
                'bars': bars,
                'shifts': shifts,
                'record_id': r.id if r else None,
                'is_swapped': cur_date in swapped_dates,
            })
            cur_date += timedelta(days=1)
            
            
            daily_rows_reversed = list(reversed(daily_rows))

        cached_stats = {
            'total_worked' : fmt_min(total_worked_min),
            'theoretical'  : fmt_min(theoretical_min),
            'month_theoretical': fmt_min(month_theoretical_min),
            'balance'      : fmt_min(balance_min),
            'balance_neg'  : balance_min < 0,
            'days_worked'  : days_with_record,
            'working_days' : working_days_in_period,
            'absences'     : absences,
            'lates'        : lates_count,
            'avg_entry'    : avg_entry or '—',
            'avg_exit'     : avg_exit  or '—',
            'avg_break'    : fmt_min(total_break_min / days_with_record) if days_with_record else '—',
            'daily_rows'   : daily_rows,
            'daily_rows_reversed': daily_rows_reversed,
        }
        

    
    import datetime
    def prev_month_range(d):
        first = d.replace(day=1)
        last_of_prev = first - datetime.timedelta(days=1)
        start = last_of_prev.replace(day=1)
        return start.strftime('%Y-%m-%d'), last_of_prev.strftime('%Y-%m-%d')
        
    def next_month_range(d):
        _, last_day = calendar.monthrange(d.year, d.month)
        last = d.replace(day=last_day)
        first_of_next = last + datetime.timedelta(days=1)
        _, next_last = calendar.monthrange(first_of_next.year, first_of_next.month)
        end = first_of_next.replace(day=next_last)
        return first_of_next.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

    prev_from, prev_to = prev_month_range(date_from)
    next_from, next_to = next_month_range(date_from)

    from pim.models import Employee as PimEmployee
    colleagues = []
    if emp and emp.sub_division:
        colleagues = PimEmployee.objects.filter(sub_division=emp.sub_division).exclude(id=emp.id)

    current_year = timezone.now().year
    current_month = timezone.now().month
    allow_next_month = (date_from.year < current_year) or (date_from.year == current_year and date_from.month < current_month)

    context = {
        'colleagues'   : list(colleagues),
        'emp'          : emp,
        'schedule'     : getattr(emp, 'work_schedule', None),
        'date_from'    : date_from,
        'date_to'      : date_to,
        'prev_from'    : prev_from,
        'prev_to'      : prev_to,
        'next_from'    : next_from,
        'next_to'      : next_to,
        'allow_next_month': allow_next_month,
        'today'        : today,
    }
    context.update(cached_stats)

    return render(request, 'attendance/my_stats.html', context)





class ShiftPatternForm(forms.ModelForm):
    class Meta:
        model = ShiftPattern
        fields = ['name', 'pattern_type', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'pattern_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

@login_required
def shift_pattern_list(request):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        messages.error(request, 'Acesso Restrito')
        return redirect('dashboard')
    patterns = ShiftPattern.objects.all()
    return render(request, 'attendance/shift_pattern_list.html', {'patterns': patterns})

@login_required
def shift_pattern_create(request):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ShiftPatternForm(request.POST)
        if form.is_valid():
            pattern = form.save()
            save_pattern_days(request, pattern)
            messages.success(request, 'Padrão de turno criado com sucesso!')
            return redirect('shift_pattern_list')
    else:
        form = ShiftPatternForm(initial={'pattern_type': ShiftPattern.TYPE_WEEKLY})
    
    return render(request, 'attendance/shift_pattern_form.html', {'form': form, 'title': 'Novo Padrão de Turno'})

@login_required
def shift_pattern_edit(request, pk):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        return redirect('dashboard')
    
    pattern = get_object_or_404(ShiftPattern, pk=pk)
    
    if request.method == 'POST':
        form = ShiftPatternForm(request.POST, instance=pattern)
        if form.is_valid():
            form.save()
            save_pattern_days(request, pattern)
            messages.success(request, 'Padrão atualizado com sucesso!')
            return redirect('shift_pattern_list')
    else:
        form = ShiftPatternForm(instance=pattern)
    
    days = list(pattern.days.all())
    return render(request, 'attendance/shift_pattern_form.html', {
        'form': form, 
        'title': 'Editar Padrão de Turno', 
        'pattern': pattern,
        'days': days
    })

@login_required
def shift_pattern_delete(request, pk):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('shift_pattern_list')
    pattern = get_object_or_404(ShiftPattern, pk=pk)
    if request.method == 'POST':
        pattern.delete()
        messages.success(request, 'Padrão removido com sucesso!')
    return redirect('shift_pattern_list')

def save_pattern_days(request, pattern):
    """Auxiliar para ler os dias postados pelo formulário e salvar."""
    pattern.days.all().delete()
    
    if pattern.pattern_type == ShiftPattern.TYPE_WEEKLY:
        
        for i in range(7):
            is_work = request.POST.get(f'day_{i}_work') == 'on'
            entry = request.POST.get(f'day_{i}_entry')
            exit_time = request.POST.get(f'day_{i}_exit')
            ShiftPatternDay.objects.create(
                pattern=pattern,
                position=i,
                is_work_day=is_work,
                entry_time=entry if is_work and entry else None,
                exit_time=exit_time if is_work and exit_time else None
            )
    else:
        
        i = 0
        while True:
            
            if f'day_{i}_is_set' not in request.POST:
                break
            is_work = request.POST.get(f'day_{i}_work') == 'on'
            entry = request.POST.get(f'day_{i}_entry')
            exit_time = request.POST.get(f'day_{i}_exit')
            ShiftPatternDay.objects.create(
                pattern=pattern,
                position=i,
                is_work_day=is_work,
                entry_time=entry if is_work and entry else None,
                exit_time=exit_time if is_work and exit_time else None
            )
            i += 1





class ShiftAssignmentForm(forms.ModelForm):
    class Meta:
        model = EmployeeShiftAssignment
        fields = ['employee', 'pattern', 'start_date', 'end_date', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'pattern': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

@login_required
def shift_assignment_list(request):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        return redirect('dashboard')
    assignments = EmployeeShiftAssignment.objects.all()
    return render(request, 'attendance/shift_assignment_list.html', {'assignments': assignments})

@login_required
def shift_assignment_create(request):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ShiftAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atribuição criada com sucesso!')
            return redirect('shift_assignment_list')
    else:
        form = ShiftAssignmentForm()
    
    return render(request, 'attendance/shift_assignment_form.html', {'form': form, 'title': 'Nova Atribuição'})

@login_required
def shift_assignment_delete(request, pk):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito.')
        return redirect('shift_assignment_list')
    assignment = get_object_or_404(EmployeeShiftAssignment, pk=pk)
    if request.method == 'POST':
        assignment.delete()
    return redirect('shift_assignment_list')





class ShiftOverrideForm(forms.ModelForm):
    class Meta:
        model = ShiftOverride
        fields = ['employee', 'date', 'override_type', 'entry_time', 'exit_time', 'reason']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'override_type': forms.Select(attrs={'class': 'form-select'}),
            'entry_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'exit_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'})
        }

@login_required
def shift_override_list(request):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        return redirect('dashboard')
    
    
    overrides = ShiftOverride.objects.select_related('employee').all()
    return render(request, 'attendance/shift_override_list.html', {'overrides': overrides})

@login_required
def shift_override_create(request):
    if not (request.user.is_admin() or request.user.is_supervisor()):
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = ShiftOverrideForm(request.POST)
        if form.is_valid():
            override = form.save(commit=False)
            override.created_by = request.user
            
            if override.override_type == ShiftOverride.TYPE_REST:
                override.entry_time = None
                override.exit_time = None
            override.save()
            messages.success(request, 'Exceção criada com sucesso!')
            return redirect('shift_override_list')
    else:
        form = ShiftOverrideForm(initial={'override_type': ShiftOverride.TYPE_WORK, 'entry_time': '08:00', 'exit_time': '16:00'})
        
    return render(request, 'attendance/shift_override_form.html', {'form': form, 'title': 'Nova Exceção de Turno'})

@login_required
def shift_override_delete(request, pk):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito.')
        return redirect('shift_override_list')
    
    override = get_object_or_404(ShiftOverride, pk=pk)
    if request.method == 'POST':
        override.delete()
        messages.success(request, 'Exceção apagada com sucesso!')
    return redirect('shift_override_list')


@login_required
def attendance_record_delete(request, pk):
    """Exclui um registro de ponto específico (se pertencer ao próprio funcionário ou admin)."""
    record = get_object_or_404(AttendanceRecord, pk=pk)
    
    if not request.user.is_admin() and not request.user.is_supervisor():
        emp = getattr(request.user, 'employee', None)
        if not emp or record.employee != emp:
            messages.error(request, 'Você não tem permissão para excluir este registro de ponto.')
            return redirect(request.META.get('HTTP_REFERER', 'attendance_stats'))
            
    date_str = record.date.strftime('%d/%m/%Y')
    record.delete()
    messages.success(request, f'Registro de ponto do dia {date_str} excluído com sucesso.')
    
    return redirect(request.META.get('HTTP_REFERER', 'attendance_stats'))


from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime

@login_required
def adjustment_approve_action(request, pk):
    from .models import AttendanceAdjustment, AttendanceRecord, AttendancePunch
    adj = get_object_or_404(AttendanceAdjustment, pk=pk)
    user = request.user

    emp_user = getattr(user, 'employee', None)
    is_supervisor = False
    if emp_user:
        is_supervisor = adj.employee.supervisors.filter(id=emp_user.id).exists()

    is_hr = getattr(user, 'role', '') == 'HR' or user.is_superuser

    if not (is_supervisor or is_hr):
        messages.error(request, 'Sem permissão para aprovar.')
        return redirect('leave_list')

    if adj.status == AttendanceAdjustment.STATUS_PENDING:
        if is_hr:
            
            adj.status = AttendanceAdjustment.STATUS_APPROVED
        elif is_supervisor:
            adj.status = AttendanceAdjustment.STATUS_SUPERVISOR_APPROVED
            adj.reviewed_at = timezone.now()
            adj.reviewed_by = user
            adj.save()
            messages.success(request, 'Ajuste aprovado pelo supervisor. Enviado para o RH.')
            return redirect('leave_list')

    elif adj.status == AttendanceAdjustment.STATUS_SUPERVISOR_APPROVED:
        if is_hr:
            adj.status = AttendanceAdjustment.STATUS_APPROVED
        else:
            messages.error(request, 'Apenas o RH pode dar a aprovação final.')
            return redirect('leave_list')

    if adj.status == AttendanceAdjustment.STATUS_APPROVED:
        
        rec, created = AttendanceRecord.objects.get_or_create(
            employee=adj.employee,
            date=adj.date
        )

        rec.punches.all().delete()
        
        default_tz = timezone.get_default_timezone()
        if isinstance(adj.requested_punches, list):
            for idx, time_str in enumerate(adj.requested_punches):
                if not time_str: continue
                try:
                    t = datetime.strptime(str(time_str), '%H:%M').time()
                except ValueError:
                    try:
                        t = datetime.strptime(str(time_str), '%H:%M:%S').time()
                    except ValueError:
                        continue
                dt = datetime.combine(adj.date, t)
                dt_aware = timezone.make_aware(dt, default_tz) if timezone.is_naive(dt) else dt
                ptype = 'IN' if idx % 2 == 0 else 'OUT'
                
                import datetime as dt
                AttendancePunch.objects.create(
                    attendance_record=rec,
                    punch_type=ptype,
                    timestamp_user=dt_aware,
                    timestamp_utc=dt_aware.astimezone(dt.timezone.utc),
                    note=f"[Ajuste Manual] {adj.reason}"
                )


        adj.attendance_record = rec
        adj.reviewed_at = timezone.now()
        adj.reviewed_by = user
        adj.save()
        messages.success(request, 'Ajuste finalizado com sucesso. O ponto foi alterado!')

    return redirect(request.META.get('HTTP_REFERER', 'leave_list'))

@login_required
def adjustment_reject_action(request, pk):
    from .models import AttendanceAdjustment
    adj = get_object_or_404(AttendanceAdjustment, pk=pk)
    user = request.user

    emp_user = getattr(user, 'employee', None)
    is_supervisor = False
    if emp_user:
        is_supervisor = adj.employee.supervisors.filter(id=emp_user.id).exists()

    is_hr = getattr(user, 'role', '') == 'HR' or user.is_superuser

    if not (is_supervisor or is_hr):
        messages.error(request, 'Sem permissão para rejeitar.')
        return redirect('leave_list')

    adj.status = AttendanceAdjustment.STATUS_REJECTED
    adj.reviewed_at = timezone.now()
    adj.reviewed_by = user
    adj.save()

    messages.success(request, 'Ajuste de ponto rejeitado.')
    return redirect(request.META.get('HTTP_REFERER', 'leave_list'))
