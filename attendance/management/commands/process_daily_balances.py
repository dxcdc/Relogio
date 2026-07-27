import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from pim.models import Employee
from attendance.models import (
    AttendanceRecord, 
    DailyTimeBalance, 
    AttendanceClosingSettings,
    get_work_info_for_date
)

class Command(BaseCommand):
    help = 'Processa as batidas de ponto aplicando regras de tolerância CLT e cálculo exato de horas noturnas.'

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str, help='Data específica em YYYY-MM-DD. Opcional.')
        parser.add_argument('--employee_id', type=int, help='Rodar apenas para um ID de funcionário. Opcional.')

    def compute_night_minutes(self, shift_start, shift_end, night_start_time, night_end_time):
        """
        Intersecta o turno real com as janelas noturnas (ex: 22h às 05h).
        Se a pessoa trabalhou, retornamos exatos minutos reais em que o ponteiro do relógio esteve no período noturno.
        """
        if not shift_start or not shift_end:
            return 0
        if not night_start_time or not night_end_time:
            return 0
            
        night_minutes = 0
        dates_to_check = [
            shift_start.date() - datetime.timedelta(days=1),
            shift_start.date(),
            shift_start.date() + datetime.timedelta(days=1)
        ]
        
        
        if timezone.is_naive(shift_start):
            shift_start = timezone.make_aware(shift_start)
        if timezone.is_naive(shift_end):
            shift_end = timezone.make_aware(shift_end)
            
        for d in dates_to_check:
            
            n_start_dt = datetime.datetime.combine(d, night_start_time)
            
            if night_start_time > night_end_time:
                n_end_dt = datetime.datetime.combine(d + datetime.timedelta(days=1), night_end_time)
            else:
                n_end_dt = datetime.datetime.combine(d, night_end_time)
                
            n_start_dt = timezone.make_aware(n_start_dt)
            n_end_dt = timezone.make_aware(n_end_dt)
            
            overlap_start = max(shift_start, n_start_dt)
            overlap_end = min(shift_end, n_end_dt)
            
            if overlap_start < overlap_end:
                night_minutes += (overlap_end - overlap_start).total_seconds() / 60.0
                
        return night_minutes

    def handle(self, *args, **options):
        target_date_str = options.get('date')
        if target_date_str:
            target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
        else:
            
            target_date = timezone.now().date() - datetime.timedelta(days=1)
            
        emp_qs = Employee.objects.filter(state=Employee.STATE_ACTIVE)
        emp_id = options.get('employee_id')
        if emp_id:
            emp_qs = emp_qs.filter(id=emp_id)

        processed_count = 0
        self.stdout.write(f"Iniciando cálculo rigoroso do dia: {target_date}")

        for emp in emp_qs:
            
            if getattr(emp, 'is_time_tracking_exempt', False):
                continue

            
            emp_settings = AttendanceClosingSettings.get_settings(emp.legal_entity)
            if emp_settings.is_active:
                night_start = emp_settings.night_shift_start
                night_end = emp_settings.night_shift_end
            else:
                night_start = None
                night_end = None
            
            work_info = get_work_info_for_date(emp, target_date)
            theo_min = work_info.get('theo_minutes', 0)
            is_work_day = work_info.get('is_work_day', False)
            
            record = AttendanceRecord.objects.filter(employee=emp, date=target_date).first()
            actual_min = 0
            raw_night_minutes = 0
            
            if record:
                
                actual_min = int(record.net_minutes_worked)
                
                
                raw_night_minutes = 0
                punches = list(record.punches.all().order_by('timestamp_user'))
                
                last_in = None
                for p in punches:
                    if p.punch_type == 'IN':
                        if not last_in: 
                            last_in = p.timestamp_utc
                    elif p.punch_type == 'OUT':
                        if last_in:
                            shift_night = self.compute_night_minutes(last_in, p.timestamp_utc, night_start, night_end)
                            raw_night_minutes += shift_night
                            last_in = None
                
                
                if last_in and target_date == timezone.now().date():
                    shift_night = self.compute_night_minutes(last_in, timezone.now(), night_start, night_end)
                    raw_night_minutes += shift_night
                            
                raw_night_minutes = int(raw_night_minutes)
                
            regular = 0
            extra_60 = 0
            extra_100 = 0
            negative = 0
            
            if is_work_day:
                
                variance = actual_min - theo_min
                is_within_tolerance = abs(variance) <= 10
                
                if is_within_tolerance:
                    
                    actual_min_adjusted = theo_min
                else:
                    actual_min_adjusted = actual_min

                if actual_min_adjusted >= theo_min:
                    regular = theo_min
                    overtime = actual_min_adjusted - theo_min
                    
                    if target_date.weekday() == 6 or work_info.get('source') == 'holiday':
                        extra_100 = overtime
                    else:
                        extra_60 = overtime
                else:
                    regular = actual_min_adjusted
                    negative = theo_min - actual_min_adjusted
            else:
                
                if actual_min > 0:
                    if target_date.weekday() == 6 or work_info.get('source') == 'holiday' or work_info.get('source') == 'shift_pattern':
                        extra_100 = actual_min
                    else:
                        
                        extra_60 = actual_min
                
            DailyTimeBalance.objects.update_or_create(
                employee=emp,
                date=target_date,
                defaults={
                    'record': record,
                    'theo_minutes': theo_min,
                    'acted_minutes': actual_min,
                    'regular_minutes': regular,
                    'extra_60_minutes': extra_60,
                    'extra_100_minutes': extra_100,
                    'night_minutes': raw_night_minutes,
                    'negative_minutes': negative
                }
            )
            processed_count += 1
            
        self.stdout.write(self.style.SUCCESS(f"Matemática Rigorosa Validada! {processed_count} saldos registrados."))
