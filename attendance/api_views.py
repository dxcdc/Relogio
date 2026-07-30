import base64
import uuid
import threading

from django.utils import timezone
from django.core.files.base import ContentFile

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import AttendanceRecord, AttendancePunch


class PunchView(APIView):
    """
    Endpoint de Ponto para o App Flutter — sistema N-batidas.

    GET  /api/v1/attendance/punch/  → Retorna estado atual do dia e lista de batidas.
    POST /api/v1/attendance/punch/  → Registra uma nova batida (IN ou OUT alternado).

    Campos aceitos no POST (multipart/form-data ou JSON):
        lat          (float, opcional)  — Latitude GPS
        lng          (float, opcional)  — Longitude GPS
        note         (str, opcional)    — Observação do funcionário
        photo_base64 (str, opcional)    — Foto em base64 (data:image/jpeg;base64,...)
    """
    permission_classes = [IsAuthenticated]

    
    
    
    def get(self, request):
        emp = getattr(request.user, 'employee', None)
        if not emp:
            return Response({'error': 'Usuário sem funcionário vinculado.'}, status=400)

        today = timezone.localdate()
        # Pre-fetch punches to eliminate the N+1 in the loop
        record = AttendanceRecord.objects.filter(employee=emp, date=today).prefetch_related('punches').first()

        punches_data = []
        current_state = None
        if record:
            current_state = record.current_state  
            # Sort in python memory to respect the prefetch
            for p in sorted(record.punches.all(), key=lambda x: x.timestamp_utc):
                punches_data.append({
                    'id': p.pk,
                    'type': p.punch_type,          
                    'label': p.get_punch_type_display(),
                    'time': p.timestamp_user.strftime('%H:%M'),
                    'timestamp': p.timestamp_user.isoformat(),
                    'is_flagged': p.is_flagged_location,
                })

        
        next_action = 'OUT' if current_state == 'IN' else 'IN'

        
        net_secs = 0
        if record:
            net_secs = int(record.net_seconds_worked)

        
        require_photo = False
        block_early = False
        block_off_days = False
        if request.user and getattr(request.user, 'role', None):
            from django.core.cache import cache as _cache
            _cache_key = f'module_perms_{request.user.pk}_{request.user.role}'
            _acc_data = _cache.get(_cache_key)
            if _acc_data is not None:
                require_photo   = _acc_data.get('attendance_photo_all_punches', False)
                block_early     = _acc_data.get('attendance_block_early_punch', False)
                block_off_days  = _acc_data.get('attendance_block_off_days', False)
            else:
                from core.models import RoleModuleAccess
                acc = RoleModuleAccess.objects.filter(role=request.user.role).first()
                if acc:
                    require_photo  = getattr(acc, 'attendance_photo_all_punches', False)
                    block_early    = getattr(acc, 'attendance_block_early_punch', False)
                    block_off_days = getattr(acc, 'attendance_block_off_days', False)

        can_punch = True
        punch_block_message = None

        if next_action == 'IN':
            from attendance.models import get_work_info_for_date
            work_info = get_work_info_for_date(request.user.employee, today)
            is_work_day = work_info.get('is_work_day', True)
            entry_time = work_info.get('entry_time')

            if block_off_days and not is_work_day:
                can_punch = False
                punch_block_message = "Hoje é seu dia de folga. Solicite uma Exceção de Turno."
            elif block_early and entry_time and not record: 
                from datetime import datetime, timedelta
                tolerance_minutes = work_info.get('tolerance_minutes', 15)
                expected_datetime = datetime.combine(today, entry_time)
                allowed_datetime = expected_datetime - timedelta(minutes=tolerance_minutes)
                if local_now.replace(tzinfo=None) < allowed_datetime:
                    can_punch = False
                    punch_block_message = f"Entrada liberada a partir das {allowed_datetime.strftime('%H:%M')}."

        return Response({
            'date': str(today),
            'current_state': current_state,   
            'next_action': next_action,        
            'total_punches': len(punches_data),
            'net_hours': record.net_hours_worked if record else '0h 00m',
            'net_seconds': net_secs,           
            'punches': punches_data,
            'require_photo_all_punches': require_photo,
            'can_punch': can_punch,
            'punch_block_message': punch_block_message,
        })

    
    
    
    def post(self, request):
        emp = getattr(request.user, 'employee', None)
        if not emp:
            return Response({'error': 'Usuário sem funcionário vinculado.'}, status=400)

        today = timezone.localdate()
        now = timezone.now()
        local_now = timezone.localtime(now)

        
        from leave.models import LeaveRequest
        if LeaveRequest.objects.filter(
            employee=emp,
            status=LeaveRequest.STATUS_APPROVED,
            from_date__lte=today,
            to_date__gte=today,
        ).exists():
            return Response(
                {'error': 'Ponto bloqueado: você possui licença/atestado aprovado hoje.'},
                status=403,
            )

        
        record = AttendanceRecord.objects.filter(employee=emp, date=today).first()
        current_state = record.current_state if record else None
        next_action = 'OUT' if current_state == 'IN' else 'IN'

        
        block_early = False
        block_off_days = False
        if request.user and getattr(request.user, 'role', None):
            from django.core.cache import cache as _cache
            _cache_key = f'module_perms_{request.user.pk}_{request.user.role}'
            _acc_data = _cache.get(_cache_key)
            if _acc_data is not None:
                block_early = _acc_data.get('attendance_block_early_punch', False)
                block_off_days = _acc_data.get('attendance_block_off_days', False)
            else:
                from core.models import RoleModuleAccess
                acc = RoleModuleAccess.objects.filter(role=request.user.role).first()
                if acc:
                    block_early = getattr(acc, 'attendance_block_early_punch', False)
                    block_off_days = getattr(acc, 'attendance_block_off_days', False)

        if next_action == 'IN':
            from attendance.models import get_work_info_for_date
            work_info = get_work_info_for_date(emp, today)
            is_work_day = work_info.get('is_work_day', True)
            entry_time = work_info.get('entry_time')

            if block_off_days and not is_work_day:
                return Response(
                    {'success': False, 'message': 'Ponto bloqueado: Hoje é seu dia de folga. Solicite uma Exceção de Turno.'},
                    status=403
                )
            elif block_early and entry_time and not record:
                from datetime import datetime, timedelta
                expected_datetime = datetime.combine(today, entry_time)
                allowed_datetime = expected_datetime - timedelta(minutes=15)
                if local_now.replace(tzinfo=None) < allowed_datetime:
                    return Response(
                        {'success': False, 'message': f"Entrada bloqueada. Liberada apenas a partir das {allowed_datetime.strftime('%H:%M')}."},
                        status=403
                    )

        if not record:
            record = AttendanceRecord.objects.create(employee=emp, date=today)

        
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        note = str(request.data.get('note', '')).strip()[:300]

        try:
            lat_f = float(lat) if lat else None
            lng_f = float(lng) if lng else None
        except (TypeError, ValueError):
            lat_f = lng_f = None

        
        photo_file = request.FILES.get('photo')
        photo_b64 = request.data.get('photo_base64', '')
        if not photo_file and photo_b64:
            try:
                format_str, imgstr = photo_b64.split(';base64,')
                ext = format_str.split('/')[-1].lower().strip()
                if ext not in ['jpeg', 'jpg', 'png', 'webp']:
                    ext = 'jpg'
                photo_file = ContentFile(
                    base64.b64decode(imgstr),
                    name=f"{emp.id}_punch_{uuid.uuid4().hex[:8]}.{ext}",
                )
            except Exception:
                pass  

        # Enforce photo rule
        config_require_all = False
        if request.user and getattr(request.user, 'role', None):
            from core.models import RoleModuleAccess
            acc = RoleModuleAccess.objects.filter(role=request.user.role).first()
            if acc:
                config_require_all = getattr(acc, 'attendance_photo_all_punches', False)

        has_punches = record.punches.exists() if record else False
        require_photo = True if not has_punches else config_require_all

        if require_photo and not photo_file:
            return Response(
                {'success': False, 'message': 'Foto obrigatória não fornecida para esta batida.'},
                status=400
            )

        
        from geopy.distance import geodesic
        is_valid_location = False
        fraud_reason = ''
        locations = emp.locations.all()

        if not locations.exists():
            is_valid_location = True  
        else:
            for loc in locations:
                has_gps = bool(loc.latitude and loc.longitude and loc.radius_meters)
                gps_ok = False

                if has_gps and lat_f and lng_f:
                    try:
                        dist = geodesic((lat_f, lng_f), (loc.latitude, loc.longitude)).meters
                        gps_ok = dist <= loc.radius_meters
                        if not gps_ok:
                            fraud_reason = (
                                f"[{loc.name}] Distância: {dist:.0f}m "
                                f"(permitido: {loc.radius_meters}m)"
                            )
                    except Exception as e:
                        fraud_reason = f"Erro GPS: {e}"
                elif not has_gps:
                    gps_ok = True  

                if gps_ok:
                    is_valid_location = True
                    fraud_reason = ''
                    break

        
        punch = AttendancePunch.objects.create(
            attendance_record=record,
            punch_type=next_action,
            timestamp_utc=now,
            timestamp_user=local_now,
            note=note,
            photo=photo_file,
            latitude=lat_f,
            longitude=lng_f,
            ip_address=None,
            location_address=None,              
            is_flagged_location=not is_valid_location,
            fraud_reason=fraud_reason if not is_valid_location else '',
        )

        
        if lat_f and lng_f:
            def _geocode(punch_id, lat, lng):
                try:
                    from geopy.geocoders import Nominatim
                    from attendance.models import AttendancePunch as _P
                    geo = Nominatim(user_agent='cdcrh_app')
                    loc_data = geo.reverse((lat, lng), timeout=5, exactly_one=True)
                    if loc_data:
                        _P.objects.filter(pk=punch_id).update(location_address=loc_data.address)
                except Exception:
                    pass
            threading.Thread(target=_geocode, args=(punch.pk, lat_f, lng_f), daemon=True).start()

        
        punches_data = []
        for p in record.punches.order_by('timestamp_utc'):
            punches_data.append({
                'id': p.pk,
                'type': p.punch_type,
                'label': p.get_punch_type_display(),
                'time': p.timestamp_user.strftime('%H:%M'),
                'timestamp': p.timestamp_user.isoformat(),
                'is_flagged': p.is_flagged_location,
            })

        label = 'Entrada/Retorno' if next_action == 'IN' else 'Saída/Pausa'

        
        require_photo = False
        if request.user and getattr(request.user, 'role', None):
            from core.models import RoleModuleAccess
            acc = RoleModuleAccess.objects.filter(role=request.user.role).first()
            if acc:
                require_photo = getattr(acc, 'attendance_photo_all_punches', False)

        # Limpa o cache do dashboard do funcionário para que o app sincronize imediatamente
        from django.core.cache import cache as _cache
        _cache.delete(f'dashboard_api_{emp.pk}')

        return Response({
            'success': True,
            'message': f'{label} registrada às {local_now.strftime("%H:%M")}.',
            'is_flagged': not is_valid_location,
            'flagged_reason': fraud_reason if not is_valid_location else None,
            'current_state': next_action,      
            'next_action': 'OUT' if next_action == 'IN' else 'IN',
            'total_punches': len(punches_data),
            'net_hours': record.net_hours_worked,
            'net_seconds': int(record.net_seconds_worked),  
            'punches': punches_data,
            'require_photo_all_punches': require_photo,
        }, status=201)


import calendar
from datetime import date, datetime

from .models import get_work_info_for_date, DailyTimeBalance

class AttendanceRecordsView(APIView):
    """
    Retorna o extrato mensal de ponto do funcionário para o App Mobile.
    GET /api/v1/attendance/records/?year=2026&month=4
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        emp = getattr(request.user, 'employee', None)
        if not emp:
            return Response({'error': 'Usuário sem funcionário vinculado.'}, status=400)

        year_str = request.query_params.get('year')
        month_str = request.query_params.get('month')
        
        today = timezone.localdate()
        
        try:
            year = int(year_str) if year_str else today.year
            month = int(month_str) if month_str else today.month
        except ValueError:
            return Response({'error': 'Ano ou mês inválido.'}, status=400)
            
        _, num_days = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, num_days)

        # ── BULK FETCH — substitui ~93 queries por ~10 ─────────────────────────
        from .models import get_work_info_for_date_range
        month_work_info = get_work_info_for_date_range(emp, start_date, end_date)

        # DailyTimeBalance do mês inteiro (1 query com select_related)
        dtb_map = {
            dtb.date: dtb
            for dtb in DailyTimeBalance.objects.filter(
                employee=emp, date__range=[start_date, end_date]
            ).select_related('record')
        }

        # AttendanceRecord do mês inteiro (1 query com prefetch de batidas)
        record_map = {}
        for r in AttendanceRecord.objects.filter(
            employee=emp, date__range=[start_date, end_date]
        ).prefetch_related('punches'):
            r._prefetched_work_info = month_work_info.get(r.date, {})
            record_map[r.date] = r

        # Prefetch de batidas para records vinculados ao DailyTimeBalance
        dtb_record_ids = [
            dtb.record_id for dtb in dtb_map.values() if dtb.record_id
        ]
        # Já estão no record_map via prefetch acima — nada extra a fazer.

        days_data = []
        missing_days = []
        total_worked_mins = 0
        total_theo_mins = 0
        total_extra_mins = 0
        total_missing_mins = 0

        def format_mins(m):
            h = int(m // 60)
            mn = int(m % 60)
            return f"{h:02d}h {mn:02d}m"

        for day in range(1, num_days + 1):
            current_date = date(year, month, day)
            w_info = month_work_info.get(current_date, {})
            dtb = dtb_map.get(current_date)

            if dtb:
                theo_mins  = dtb.theo_minutes
                worked_mins = dtb.acted_minutes
                extra  = dtb.extra_60_minutes + dtb.extra_100_minutes
                missing = dtb.negative_minutes

                first_in_str = "--:--"
                last_out_str = "--:--"
                record_id = None
                punches_list = []
                # record já vem do record_map (prefetchado) ou do dtb.record
                rec = record_map.get(current_date) or (dtb.record if dtb.record_id else None)
                if rec:
                    record_id = rec.id
                    punches = sorted(list(rec.punches.all()), key=lambda p: p.timestamp_user)
                    punches_list = [timezone.localtime(p.timestamp_user).strftime('%H:%M') for p in punches]
                    if punches:
                        first_in  = next((p for p in punches if p.punch_type == 'IN'), None)
                        last_out  = next((p for p in reversed(punches) if p.punch_type == 'OUT'), None)
                        if first_in:
                            first_in_str = timezone.localtime(first_in.timestamp_user).strftime('%H:%M')
                        if last_out:
                            last_out_str = timezone.localtime(last_out.timestamp_user).strftime('%H:%M')
            else:
                # Usa dados do bulk fetch — zero queries extras
                theo_mins  = w_info.get('theo_minutes', 0)
                record = record_map.get(current_date)
                worked_mins = (record.net_seconds_worked / 60.0) if record else 0.0
                extra   = max(0, worked_mins - theo_mins) if worked_mins > theo_mins else 0
                missing = max(0, theo_mins - worked_mins) if theo_mins > worked_mins and current_date <= today else 0

                first_in_str = "--:--"
                last_out_str = "--:--"
                record_id = None
                punches_list = []
                if record:
                    record_id = record.id
                    punches = sorted(list(record.punches.all()), key=lambda p: p.timestamp_user)
                    punches_list = [timezone.localtime(p.timestamp_user).strftime('%H:%M') for p in punches]
                    if punches:
                        first_in  = next((p for p in punches if p.punch_type == 'IN'), None)
                        last_out  = next((p for p in reversed(punches) if p.punch_type == 'OUT'), None)
                        if first_in:
                            first_in_str = timezone.localtime(first_in.timestamp_user).strftime('%H:%M')
                        if last_out:
                            last_out_str = timezone.localtime(last_out.timestamp_user).strftime('%H:%M')

            total_worked_mins += worked_mins
            total_theo_mins   += theo_mins
            total_extra_mins  += extra
            total_missing_mins += missing

            tags = []
            if current_date > today:
                pass
            elif w_info.get('source') == 'leave':
                tags = ['LICENCA']
            elif w_info.get('source') == 'holiday':
                tags = ['FERIADO']
            elif theo_mins == 0 and worked_mins == 0:
                tags.append('FOLGA')
            elif theo_mins > 0 and worked_mins == 0 and current_date < today:
                tags.append('FALTA')
            elif extra > 0:
                tags.append('HORA_EXTRA')

            entry_t = w_info.get('entry_time')
            exit_t  = w_info.get('exit_time')
            shift_time = f"{entry_t.strftime('%H:%M')} - {exit_t.strftime('%H:%M')}" if entry_t and exit_t else ""
            day_title  = w_info.get('title', '')

            progress = 0.0
            if theo_mins > 0:
                progress = min(1.0, worked_mins / theo_mins)
            elif worked_mins > 0:
                progress = 1.0

            days_data.append({
                'date': current_date.isoformat(),
                'record_id': record_id,
                'punches': punches_list,
                'worked_time': format_mins(worked_mins) if current_date <= today else '',
                'theo_time': format_mins(theo_mins),
                'progress': progress,
                'tags': tags,
                'shift_time': shift_time,
                'day_title': day_title,
            })

            if missing > 0:
                weekdays_pt = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom']
                wd_str = weekdays_pt[current_date.weekday()]
                missing_days.append({
                    'date': f"{wd_str}, {current_date.strftime('%d/%m/%Y')}",
                    'hours': f"- {format_mins(missing)}"
                })

        missing_days.reverse()

        def format_total(m):
            h = int(m // 60)
            mn = int(m % 60)
            return f"{h}h {mn:02d}m"

        return Response({
            'year': year,
            'month': month,
            'month_progress': min(1.0, total_worked_mins / total_theo_mins) if total_theo_mins > 0 else 0.0,
            'total_worked': format_total(total_worked_mins),
            'total_theo': format_total(total_theo_mins),
            'total_extra': format_total(total_extra_mins),
            'total_missing': format_total(total_missing_mins),
            'balance_minutes': total_extra_mins - total_missing_mins,
            'days': days_data,
            'missing_days': missing_days,
        })

from .models import AttendanceAdjustment

class AttendanceRecordDeleteView(APIView):
    """
    Exclui um registro de ponto.
    DELETE /api/v1/attendance/records/<id>/
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        emp = getattr(request.user, 'employee', None)
        if not emp:
            return Response({'error': 'Usuário sem funcionário vinculado.'}, status=400)
            
        record = AttendanceRecord.objects.filter(id=pk, employee=emp).first()
        if not record:
            return Response({'error': 'Registro não encontrado ou você não tem permissão.'}, status=404)
            
        record.delete()
        return Response({'success': True, 'message': 'Registro excluído com sucesso.'})


class AttendanceAdjustmentCreateView(APIView):
    """
    Cria uma solicitação de ajuste de ponto (enviado para o RH).
    POST /api/v1/attendance/adjustments/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        emp = getattr(request.user, 'employee', None)
        if not emp:
            return Response({'error': 'Usuário sem funcionário vinculado.'}, status=400)
            
        data = request.data
        date_str = data.get('date')
        reason = data.get('reason')
        punches = data.get('punches', [])
        
        if not date_str or not reason:
            return Response({'error': 'Data e motivo são obrigatórios.'}, status=400)
            
        try:
            adj_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Formato de data inválido. Use YYYY-MM-DD.'}, status=400)
            
        adj = AttendanceAdjustment.objects.create(
            employee=emp,
            date=adj_date,
            requested_punches=punches,
            reason=reason,
            status='PENDING'
        )
        
        return Response({
            'success': True, 
            'message': 'Ajuste solicitado com sucesso!',
            'adjustment_id': adj.id
        }, status=201)

from leave.models import LeaveRequest
from .models import ShiftSwapRequest

class MyRequestsView(APIView):
    """
    Retorna todas as solicitações (Licenças, Trocas e Ajustes) do usuário.
    GET /api/v1/attendance/my-requests/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        emp = getattr(request.user, 'employee', None)
        if not emp:
            return Response({'error': 'Usuário sem funcionário vinculado.'}, status=400)

        
        leaves_qs = LeaveRequest.objects.filter(employee=emp).select_related('leave_type').order_by('-date_applied')
        leaves_data = []
        for l in leaves_qs:
            leaves_data.append({
                'id': l.id,
                'type': l.leave_type.name if l.leave_type else 'Licença',
                'from_date': l.from_date.isoformat(),
                'to_date': l.to_date.isoformat(),
                'date_applied': l.date_applied.isoformat(),
                'status': l.status,
                'status_display': l.get_status_display(),
                'has_attachment': bool(l.attachment),
            })

        
        swaps_qs = ShiftSwapRequest.objects.filter(requester=emp).select_related('target_employee').order_by('-created_at')
        swaps_data = []
        for s in swaps_qs:
            swaps_data.append({
                'id': s.id,
                'target_employee': s.target_employee.full_name if s.target_employee else 'Desconhecido',
                'date': s.date.isoformat(),
                'created_at': s.created_at.isoformat(),
                'status': s.status,
                'status_display': s.get_status_display(),
                'reason': s.reason,
            })

        
        adjustments_qs = AttendanceAdjustment.objects.filter(employee=emp).order_by('-created_at')
        adjustments_data = []
        for a in adjustments_qs:
            adjustments_data.append({
                'id': a.id,
                'date': a.date.isoformat(),
                'created_at': a.created_at.isoformat(),
                'status': a.status,
                'status_display': a.get_status_display(),
                'reason': a.reason,
                'requested_punches': a.requested_punches,
            })

        return Response({
            'leaves': leaves_data,
            'swaps': swaps_data,
            'adjustments': adjustments_data,
        })

from .models import ShiftOverride
from pim.models import Employee

class SwapInboxView(APIView):
    """
    Retorna a caixa de entrada de trocas de turno e colegas do setor.
    GET /api/v1/attendance/swaps/inbox/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        emp = getattr(user, 'employee', None)
        
        qs = ShiftSwapRequest.objects.select_related('requester', 'target_employee').order_by('-created_at')
        from django.db.models import Q
        combined = []
        if emp:
            combined = list(qs.filter(Q(requester=emp) | Q(target_employee=emp)))
            
        combined.sort(key=lambda x: x.created_at, reverse=True)
        
        def format_swap(s):
            return {
                'id': s.id,
                'requester_name': s.requester.full_name if s.requester else 'Desconhecido',
                'target_name': s.target_employee.full_name if s.target_employee else 'Desconhecido',
                'date': s.date.isoformat(),
                'created_at': s.created_at.isoformat(),
                'status': s.status,
                'status_display': s.get_status_display(),
                'reason': s.reason,
                'is_requester': emp and s.requester == emp,
                'is_target': emp and s.target_employee == emp,
            }
            
        swaps_data = [format_swap(s) for s in combined]
        
        
        colleagues_data = []
        if emp and emp.sub_division:
            colleagues = Employee.objects.filter(sub_division=emp.sub_division, user__is_active=True).exclude(id=emp.id)
            
            
            if getattr(emp.sub_division, 'supervisor', None):
                colleagues = colleagues.exclude(id=emp.sub_division.supervisor.id)
            colleagues = colleagues.exclude(user__role__in=['Admin', 'HR', 'Supervisor'])
            
            for c in colleagues:
                colleagues_data.append({
                    'id': c.id,
                    'name': c.full_name
                })
                
        return Response({
            'swaps': swaps_data,
            'colleagues': colleagues_data,
        })

class SwapRequestCreateView(APIView):
    """
    Cria uma solicitação de troca.
    POST /api/v1/attendance/swaps/create/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        my_emp = getattr(request.user, 'employee', None)
        if not my_emp:
            return Response({'error': 'Usuário não tem funcionário associado.'}, status=400)
            
        if not my_emp.sub_division:
            return Response({'error': 'Você não tem um setor definido.'}, status=400)
            
        if not my_emp.sub_division.allow_shift_swaps:
            return Response({'error': 'O seu departamento não permite trocas de turno.'}, status=400)
            
        role_access_data = getattr(my_emp, 'get_role_access', lambda: None)()
        if role_access_data and not role_access_data.get('swap', True):
            return Response({'error': 'O seu cargo/perfil não tem permissão para realizar trocas de turno.'}, status=400)
            
        data = request.data
        target_id = data.get('target_employee_id')
        date_str = data.get('date')
        reason = data.get('reason', '')
        
        if not target_id or not date_str:
            return Response({'error': 'Dados incompletos.'}, status=400)
            
        target_emp = Employee.objects.filter(pk=target_id).first()
        if not target_emp:
            return Response({'error': 'Colega não encontrado.'}, status=404)
            
        if target_emp.sub_division != my_emp.sub_division:
            return Response({'error': 'Só é permitido trocar turno com funcionários do mesmo setor.'}, status=400)
            
        exists = ShiftSwapRequest.objects.filter(requester=my_emp, date=date_str).exclude(status__in=['APPROVED', 'REJECTED']).exists()
        if exists:
            return Response({'error': 'Você já possui uma solicitação pendente para este dia.'}, status=400)
            
        try:
            req = ShiftSwapRequest.objects.create(
                requester=my_emp,
                target_employee=target_emp,
                date=date_str,
                reason=reason,
                status='PENDING_TARGET'
            )
            return Response({'success': True, 'message': 'Solicitação enviada! Aguardando o aceite do seu colega.', 'id': req.id}, status=201)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class SwapRequestResolveView(APIView):
    """
    Aprova ou rejeita uma solicitação.
    POST /api/v1/attendance/swaps/resolve/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        emp = getattr(user, 'employee', None)
        
        data = request.data
        req_id = data.get('request_id')
        action = data.get('action') 
        
        if not req_id or not action:
            return Response({'error': 'Parâmetros request_id e action são obrigatórios.'}, status=400)
            
        try:
            req_obj = ShiftSwapRequest.objects.get(pk=req_id)
        except ShiftSwapRequest.DoesNotExist:
            return Response({'error': 'Solicitação não encontrada.'}, status=404)
            
        if req_obj.status in ['APPROVED', 'REJECTED']:
            return Response({'error': 'Solicitação já finalizada.'}, status=400)
            
        if action == 'REJ':
            can_reject = False
            if req_obj.status == 'PENDING_TARGET' and req_obj.target_employee == emp:
                can_reject = True
            elif req_obj.status == 'PENDING_SUPERVISOR' and user.is_supervisor():
                can_reject = True
            elif req_obj.status == 'PENDING_HR' and user.is_admin():
                can_reject = True
                
            if not can_reject:
                return Response({'error': 'Você não tem permissão para rejeitar no status atual.'}, status=403)
                
            req_obj.status = 'REJECTED'
            req_obj.resolved_by = user
            req_obj.resolved_at = timezone.now()
            req_obj.save()
            return Response({'success': True, 'message': 'Solicitação rejeitada.'})
            
        if action == 'APP':
            if req_obj.status == 'PENDING_TARGET':
                if req_obj.target_employee != emp:
                    return Response({'error': 'Apenas o colega alvo pode aceitar essa etapa.'}, status=403)
                req_obj.status = 'PENDING_SUPERVISOR'
                req_obj.save()
                return Response({'success': True, 'message': 'Troca aceita! Encaminhada para o Supervisor.'})
                
            elif req_obj.status == 'PENDING_SUPERVISOR':
                if not user.is_supervisor():
                    return Response({'error': 'Acesso restrito a supervisores.'}, status=403)
                req_obj.status = 'PENDING_HR'
                req_obj.save()
                return Response({'success': True, 'message': 'Troca autorizada! Encaminhada para o RH.'})
                
            elif req_obj.status == 'PENDING_HR':
                if not user.is_admin():
                    return Response({'error': 'Acesso restrito ao RH.'}, status=403)
                    
                maria = req_obj.requester
                joao = req_obj.target_employee
                
                if not maria.work_schedule or not joao.work_schedule:
                    return Response({'error': 'Ambos os funcionários precisam ter uma Escala Base cadastrada para gerar a troca.'}, status=400)
                    
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
                return Response({'success': True, 'message': 'Troca Aprovada e efetivada!'})
                
        return Response({'error': 'Ação inválida.'}, status=400)


class TimeBankAPIView(APIView):
    """
    Retorna o extrato do Banco de Horas em JSON para o App Mobile.
    GET /api/v1/attendance/timebank/?year=2026&month=5
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = getattr(request.user, 'employee', None)
        if not employee:
            return Response({'error': 'Perfil de funcionário não encontrado.'}, status=400)

        import datetime as dt
        today = dt.date.today()

        try:
            req_year = int(request.query_params.get('year', today.year))
            req_month = int(request.query_params.get('month', today.month))
        except (ValueError, TypeError):
            req_year, req_month = today.year, today.month

        def fmt_hm(minutes):
            sign = '+' if minutes >= 0 else '-'
            m = int(abs(minutes))
            h, r = m // 60, m % 60
            return f'{sign}{h:02d}h {r:02d}m'

        from .models import get_work_info_for_date_range
        
        import calendar as cal
        _, last_day = cal.monthrange(req_year, req_month)
        start_date = dt.date(req_year, req_month, 1)
        end_date = dt.date(req_year, req_month, last_day)

        month_work_info = get_work_info_for_date_range(employee, start_date, end_date)

        records_qs = AttendanceRecord.objects.filter(
            employee=employee,
            date__range=[start_date, end_date]
        ).prefetch_related('punches')
        
        record_map = {}
        for r in records_qs:
            r._prefetched_work_info = month_work_info.get(r.date, {})
            record_map[r.date] = r

        end_day = today.day if (req_year == today.year and req_month == today.month) else last_day

        month_theo = month_acted = month_extra = month_negative = 0
        transactions = []

        month_names_pt = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                          "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        weekdays_pt = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]

        for d in range(1, end_day + 1):
            target_date = dt.date(req_year, req_month, d)
            work_info = month_work_info.get(target_date, {})
            theo_min = work_info.get('theo_minutes', 0)
            tol_min = work_info.get('tolerance_minutes', 0)

            record = record_map.get(target_date)
            acted_min = record.net_minutes_worked if record else 0

            month_theo += theo_min
            month_acted += acted_min

            daily_diff = acted_min - theo_min
            wd_str = weekdays_pt[target_date.weekday()]
            date_label = f"{wd_str}, {target_date.strftime('%d/%m')}"

            if daily_diff > tol_min:
                month_extra += daily_diff
                transactions.append({
                    'date': target_date.isoformat(),
                    'date_label': date_label,
                    'type': 'extra',
                    'minutes': int(daily_diff),
                    'display': fmt_hm(int(daily_diff)),
                })
            elif daily_diff < -tol_min and theo_min > 0:
                cost = abs(daily_diff)
                month_negative += cost
                transactions.append({
                    'date': target_date.isoformat(),
                    'date_label': date_label,
                    'type': 'negative',
                    'minutes': -int(cost),
                    'display': fmt_hm(-int(cost)),
                })

        balance = month_extra - month_negative
        progress = min(100, int((month_acted / month_theo * 100) if month_theo > 0 else 0))

        transactions.reverse()

        return Response({
            'year': req_year,
            'month': req_month,
            'month_name': f"{month_names_pt[req_month - 1]} {req_year}",
            'balance_minutes': int(balance),
            'balance_display': fmt_hm(int(balance)),
            'balance_positive': balance >= 0,
            'theo_display': fmt_hm(int(month_theo)).replace('+', '').strip(),
            'extra_display': fmt_hm(int(month_extra)).replace('+', '').strip(),
            'negative_display': fmt_hm(-int(month_negative)).replace('+', '').strip() if month_negative else '00h 00m',
            'progress_percent': progress,
            'transactions': transactions,
        })
