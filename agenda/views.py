import json
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime
from django.db import models

from core.decorators import require_module
from pim.models import Employee
from admin_app.models import Location, City, Subunit
from .models import Event, QuickNote, EventType

@login_required
@require_module('agenda')
def calendar_view(request):
    """
    Renders the beautiful corporate calendar interface.
    Provides necessary context like employees list, departments, locations, and cities.
    """
    employee = getattr(request.user, 'employee', None)
    
    # Context data for the event creation/edit modals
    all_employees = Employee.objects.filter(status='ACTIVE') if hasattr(Employee.objects, 'status') else Employee.objects.all()
    # Ensure active sorting and formatting
    all_employees = all_employees.order_by('first_name', 'last_name')
    
    locations = Location.objects.all().order_by('name')
    cities = City.objects.all().order_by('name')
    subunits = Subunit.objects.all().order_by('name')
    
    # Seed default EventType if none exist
    if not EventType.objects.exists():
        default_types = [
            ('Reunião', '#3b82f6'),
            ('Integração', '#10b981'),
            ('Entrevista', '#f59e0b'),
            ('Treinamento', '#8b5cf6'),
            ('Visita Técnica', '#ef4444'),
            ('Outro', '#64748b'),
        ]
        for name, color in default_types:
            EventType.objects.create(name=name, color=color)
            
    event_types = EventType.objects.all().order_by('name')
    
    # Personal quick notes for the side panel
    quick_notes = QuickNote.objects.filter(user=request.user).select_related('referenced_event')
    open_events = Event.objects.filter(status__in=['aberto', 'agendado']).order_by('-start_date')

    # URL publica do calendario corporativo Google para assinatura
    try:
        from attendance.google_sync import get_corporate_calendar_subscribe_url
        google_subscribe_url = get_corporate_calendar_subscribe_url()
    except Exception:
        google_subscribe_url = None

    # Status da integracao Google corporativa (usado para o banner na agenda)
    try:
        import os
        from core.models import GoogleIntegration, OrangeUser as _OrangeUser
        _corp_owner = os.environ.get('GOOGLE_CORP_CALENDAR_OWNER', 'admin')
        _corp_user  = _OrangeUser.objects.filter(username=_corp_owner).first()
        google_integration = GoogleIntegration.objects.filter(user=_corp_user).first() if _corp_user else None
    except Exception:
        google_integration = None

    context = {
        'employee': employee,
        'all_employees': all_employees,
        'locations': locations,
        'cities': cities,
        'subunits': subunits,
        'event_types': event_types,
        'quick_notes': quick_notes,
        'open_events': open_events,
        'google_subscribe_url': google_subscribe_url,
        'google_integration': google_integration,
    }
    return render(request, 'agenda/calendar.html', context)


@login_required
@require_module('agenda')
def list_events(request):
    """
    JSON endpoint that returns events within the requested start and end dates.
    """
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    
    events = Event.objects.all()
    
    if start_str:
        start_date = parse_datetime(start_str)
        if start_date:
            events = events.filter(start_date__gte=start_date)
    if end_str:
        end_date = parse_datetime(end_str)
        if end_date:
            events = events.filter(end_date__lte=end_date)
            
    # Map event type lowercased names to their active database colors dynamically
    types_map = {t.name.lower(): t.color for t in EventType.objects.all()}
    
    event_list = []
    for e in events:
        participants = [
            {'id': emp.id, 'name': f"{emp.first_name} {emp.last_name}"}
            for emp in e.employees.all()
        ]
        
        can_edit = request.user.is_admin() or request.user.is_hr() or (e.organizer and getattr(request.user, 'employee', None) == e.organizer)
        # Use dynamic category color from EventType chosen by the user in the database
        category_color = types_map.get(e.event_type.lower(), e.color)
        
        event_list.append({
            'id': e.id,
            'title': e.title,
            'start': e.start_date.isoformat(),
            'end': e.end_date.isoformat() if e.end_date else None,
            'color': category_color,
            'description': e.notes or '',
            'editable': can_edit,
            'extendedProps': {
                'eventType': e.event_type,
                'eventTypeDisplay': e.get_event_type_display(),
                'organizerId': e.organizer.id if e.organizer else None,
                'organizerName': f"{e.organizer.first_name} {e.organizer.last_name}" if e.organizer else "N/A",
                'locationId': e.location.id if e.location else None,
                'locationName': e.location.name if e.location else '',
                'cityId': e.city.id if e.city else None,
                'cityName': e.city.name if e.city else '',
                'status': e.status,
                'statusDisplay': e.get_status_display(),
                'participants': participants,
                'canEdit': can_edit,
                'meetingLink': getattr(e, 'meeting_link', '') or '',
                'externalParticipants': getattr(e, 'external_participants', '') or ''
            }
        })
        
    return JsonResponse(event_list, safe=False)

def send_event_invitation_emails(event, participants, is_update=False):
    """
    Envia e-mails de convite/atualização para:
    - Todos os colaboradores internos (participants queryset)
    - Todos os convidados externos (event.external_participants, separados por vírgula)
    """
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.conf import settings
    import logging
    logger = logging.getLogger(__name__)

    organizer_name = f"{event.organizer.first_name} {event.organizer.last_name}" if event.organizer else "Netline RH"

    # Formata a data/hora de exibição
    start_str = event.start_date.strftime("%d/%m/%Y às %H:%M")
    end_str = event.end_date.strftime("%d/%m/%Y às %H:%M") if event.end_date else ""

    hide_end_time = False
    if event.event_type and event.event_type.lower() in ['entrevista', 'teste psicológico', 'teste prático']:
        hide_end_time = True
    elif 'entrevista' in event.title.lower() or 'teste' in event.title.lower() or 'avaliação' in event.title.lower() or 'avaliacao' in event.title.lower():
        hide_end_time = True

    if hide_end_time:
        date_time_str = start_str
    else:
        if end_str:
            if event.start_date.date() == event.end_date.date():
                date_time_str = f"{start_str} até {event.end_date.strftime('%H:%M')}"
            else:
                date_time_str = f"{start_str} até {end_str}"
        else:
            date_time_str = start_str

    location_str = ""
    if event.location:
        location_str += event.location.name
    if event.city:
        if location_str:
            location_str += " — "
        location_str += event.city.name

    subject = f"[Atualização] {event.title}" if is_update else f"Convite: {event.title}"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@netlineplay.com.br')

    event_type_lower = event.event_type.lower() if event.event_type else ''
    is_recruitment = event_type_lower in ['entrevista', 'teste psicológico', 'teste prático']
    recruitment_type = event_type_lower.title() if is_recruitment else ""

    def _send(first_name, email_address, is_external=False):
        """Envia o e-mail para um destinatário."""
        try:
            context = {
                'first_name': first_name,
                'title': event.title,
                'date_time_str': date_time_str,
                'organizer_name': organizer_name,
                'location_str': location_str,
                'meeting_link': event.meeting_link or '',
                'notes': event.notes or '',
                'is_update': is_update,
                'is_recruitment': is_recruitment,
                'recruitment_type': recruitment_type,
                'is_external': is_external,
            }
            html_content = render_to_string('email/event_invitation.html', context)
            plain_text_parts = [
                f"Ola, {first_name}!\n",
                f"{'O compromisso foi atualizado.' if is_update else 'Voce foi convidado(a) para um compromisso.'}\n",
                f"\n{event.title}\n",
                f"Data/Hora: {date_time_str}\n",
                f"Organizador: {organizer_name}\n",
            ]
            if location_str:
                plain_text_parts.append(f"Local: {location_str}\n")
            if event.meeting_link:
                plain_text_parts.append(f"Link: {event.meeting_link}\n")
            plain_text_parts.append("\nAcesse a agenda: https://poeirao.netlineplay.com.br/agenda/\n")
            plain_text = "".join(plain_text_parts)

            from emails.utils import send_custom_email
            
            # Para o template customizado, usamos context já criado
            sent = send_custom_email('event_invitation', context, email_address)
            
            if not sent:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_text,
                    from_email=from_email,
                    to=[email_address],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=True)
            logger.info(f"[Agenda] E-mail de convite enviado para {email_address}")
        except Exception as e:
            logger.error(f"[Agenda] Falha ao enviar e-mail para {email_address}: {e}")

    # 1. Colaboradores internos
    for employee in participants:
        if not employee.work_email:
            continue
        first_name = employee.first_name or employee.username or "Colaborador"
        _send(first_name, employee.work_email, is_external=False)

    # 2. Convidados externos (e-mails separados por vírgula ou ponto-e-vírgula)
    if event.external_participants:
        raw = event.external_participants.replace(';', ',')
        external_emails = [e.strip() for e in raw.split(',') if e.strip() and '@' in e.strip()]
        for ext_email in external_emails:
            # Usa a parte antes do @ como nome amigável se possível
            friendly_name = ext_email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
            _send(friendly_name, ext_email, is_external=True)


@login_required
@require_module('agenda')
@require_POST
def create_event(request):
    """
    JSON endpoint to create a new event.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido.'}, status=400)

    title = data.get('title')
    start_str = data.get('start_date')
    end_str = data.get('end_date')
    
    if not title or not start_str or not end_str:
        return JsonResponse({'status': 'error', 'message': 'Título, data de início e término são obrigatórios.'}, status=400)
        
    start_date = parse_datetime(start_str)
    end_date = parse_datetime(end_str)
    
    if not start_date or not end_date:
        return JsonResponse({'status': 'error', 'message': 'Formato de data inválido.'}, status=400)

    employee = getattr(request.user, 'employee', None)
    if not employee and not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Apenas colaboradores podem criar eventos.'}, status=403)

    location_id = data.get('location')
    city_id = data.get('city')
    
    location = Location.objects.filter(id=location_id).first() if location_id else None
    city = City.objects.filter(id=city_id).first() if city_id else None

    event_type_name = data.get('event_type', 'reuniao')
    event_type_obj = EventType.objects.filter(name__iexact=event_type_name).first()
    chosen_color = event_type_obj.color if event_type_obj else data.get('color', '#3b82f6')

    recurrence = data.get('recurrence', 'none')

    event = Event.objects.create(
        title=title,
        event_type=event_type_name,
        organizer=employee,
        location=location,
        city=city,
        start_date=start_date,
        end_date=end_date,
        notes=data.get('notes', ''),
        color=chosen_color,
        status=data.get('status', 'agendado'),
        meeting_link=data.get('meeting_link', ''),
        external_participants=data.get('external_participants', ''),
        recurrence=recurrence,
    )

    participant_ids = data.get('employees', [])
    employees_qs = Employee.objects.none()
    if participant_ids:
        employees_qs = Employee.objects.filter(id__in=participant_ids)
        event.employees.set(employees_qs)
        
    if participant_ids or event.external_participants:
        send_event_invitation_emails(event, employees_qs, is_update=False)

    # --- Gerar eventos recorrentes ---
    if recurrence != 'none':
        duration = end_date - start_date
        if recurrence == 'daily':
            occurrences = [(timedelta(days=i)) for i in range(1, 31)]
        elif recurrence == 'weekly':
            occurrences = [(timedelta(weeks=i)) for i in range(1, 13)]
        elif recurrence == 'monthly':
            occurrences = [(timedelta(days=30 * i)) for i in range(1, 7)]
        else:
            occurrences = []

        for delta in occurrences:
            child = Event.objects.create(
                title=title,
                event_type=event_type_name,
                organizer=employee,
                location=location,
                city=city,
                start_date=start_date + delta,
                end_date=end_date + delta,
                notes=data.get('notes', ''),
                color=chosen_color,
                status='agendado',
                meeting_link=data.get('meeting_link', ''),
                external_participants=data.get('external_participants', ''),
                recurrence='none',
                recurrence_parent=event,
            )
            if participant_ids:
                child.employees.set(employees_qs)

    # Sincroniza o compromisso com o Google Calendar se o organizador possuir integração ativa
    try:
        from attendance.google_sync import sync_corporate_event_to_google
        sync_corporate_event_to_google(event)
    except Exception as sync_err:
        import logging
        logging.getLogger(__name__).error(f"Erro ao sincronizar evento criado com o Google Calendar: {sync_err}")

    return JsonResponse({
        'status': 'success',
        'message': 'Evento criado com sucesso!',
        'event': {
            'id': event.id,
            'title': event.title,
            'start': event.start_date.isoformat(),
            'end': event.end_date.isoformat()
        }
    })


@login_required
@require_module('agenda')
@require_POST
def update_event(request, event_id):
    """
    JSON endpoint to update an existing event. Can also be called on drag-and-drop.
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Check permissions
    can_edit = request.user.is_admin() or request.user.is_hr() or (event.organizer and getattr(request.user, 'employee', None) == event.organizer)
    if not can_edit:
        return JsonResponse({'status': 'error', 'message': 'Você não tem permissão para editar este evento.'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido.'}, status=400)

    # FullCalendar drag-and-drop might only send start_date & end_date
    is_drag_drop = data.get('is_drag_drop', False)
    
    if is_drag_drop:
        start_str = data.get('start_date')
        end_str = data.get('end_date')
        if start_str:
            event.start_date = parse_datetime(start_str)
        if end_str:
            event.end_date = parse_datetime(end_str)
        event.save()
        
        # Envia e-mails de atualização ao reagendar via drag-and-drop
        send_event_invitation_emails(event, event.employees.all(), is_update=True)
        
        # Sincroniza com Google Calendar
        try:
            from attendance.google_sync import sync_corporate_event_to_google
            sync_corporate_event_to_google(event)
        except Exception as sync_err:
            import logging
            logging.getLogger(__name__).error(f"Erro ao sincronizar evento arrastado com o Google Calendar: {sync_err}")
            
        return JsonResponse({'status': 'success', 'message': 'Evento atualizado com sucesso!'})

    # Standard full form update
    title = data.get('title')
    start_str = data.get('start_date')
    end_str = data.get('end_date')
    
    if not title or not start_str or not end_str:
        return JsonResponse({'status': 'error', 'message': 'Título, data de início e término são obrigatórios.'}, status=400)

    start_date = parse_datetime(start_str)
    end_date = parse_datetime(end_str)
    
    if not start_date or not end_date:
        return JsonResponse({'status': 'error', 'message': 'Formato de data inválido.'}, status=400)

    location_id = data.get('location')
    city_id = data.get('city')
    
    event_type_name = data.get('event_type', event.event_type)
    event_type_obj = EventType.objects.filter(name__iexact=event_type_name).first()
    chosen_color = event_type_obj.color if event_type_obj else data.get('color', event.color)

    event.title = title
    event.event_type = event_type_name
    event.location = Location.objects.filter(id=location_id).first() if location_id else None
    event.city = City.objects.filter(id=city_id).first() if city_id else None
    event.start_date = start_date
    event.end_date = end_date
    event.notes = data.get('notes', '')
    event.meeting_link = data.get('meeting_link', '')
    event.external_participants = data.get('external_participants', '')
    event.color = chosen_color
    event.status = data.get('status', event.status)
    event.save()

    participant_ids = data.get('employees', [])
    employees_qs = Employee.objects.none()
    if participant_ids:
        employees_qs = Employee.objects.filter(id__in=participant_ids)
        event.employees.set(employees_qs)
    else:
        event.employees.clear()

    if participant_ids or event.external_participants:
        send_event_invitation_emails(event, employees_qs, is_update=True)

    # Sincroniza com Google Calendar
    try:
        from attendance.google_sync import sync_corporate_event_to_google
        sync_corporate_event_to_google(event)
    except Exception as sync_err:
        import logging
        logging.getLogger(__name__).error(f"Erro ao sincronizar evento atualizado com o Google Calendar: {sync_err}")

    return JsonResponse({'status': 'success', 'message': 'Evento atualizado com sucesso!'})


@login_required
@require_module('agenda')
@require_POST
def delete_event(request, event_id):
    """
    JSON endpoint to delete an event.
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Check permissions
    can_delete = request.user.is_admin() or request.user.is_hr() or (event.organizer and getattr(request.user, 'employee', None) == event.organizer)
    if not can_delete:
        return JsonResponse({'status': 'error', 'message': 'Você não tem permissão para excluir este evento.'}, status=403)

    # Remove do Google Calendar
    try:
        from attendance.google_sync import delete_corporate_event_from_google
        delete_corporate_event_from_google(event)
    except Exception as sync_err:
        import logging
        logging.getLogger(__name__).error(f"Erro ao excluir evento do Google Calendar: {sync_err}")

    event.delete()
    return JsonResponse({'status': 'success', 'message': 'Evento excluído com sucesso!'})


@login_required
@require_module('agenda')
@require_POST
def create_quick_note(request):
    """
    JSON endpoint to create a quick note.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido.'}, status=400)

    title = data.get('title', 'Nota Sem Título')
    content = data.get('content')
    referenced_event_id = data.get('referenced_event_id')
    
    if not content:
        return JsonResponse({'status': 'error', 'message': 'Conteúdo da nota é obrigatório.'}, status=400)

    referenced_event = None
    if referenced_event_id:
        try:
            referenced_event = Event.objects.get(id=referenced_event_id)
        except Event.DoesNotExist:
            pass

    note = QuickNote.objects.create(
        user=request.user,
        title=title,
        content=content,
        referenced_event=referenced_event
    )

    return JsonResponse({
        'status': 'success',
        'message': 'Nota criada!',
        'note': {
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'created_at': note.created_at.strftime('%d/%m/%Y %H:%M'),
            'referenced_event': {
                'id': note.referenced_event.id,
                'title': note.referenced_event.title,
                'color': note.referenced_event.color or '#3b82f6'
            } if note.referenced_event else None
        }
    })


@login_required
@require_module('agenda')
@require_POST
def delete_quick_note(request, note_id):
    """
    JSON endpoint to delete a quick note.
    """
    note = get_object_or_404(QuickNote, id=note_id, user=request.user)
    note.delete()
    return JsonResponse({'status': 'success', 'message': 'Nota excluída!'})


@login_required
@require_module('agenda')
@require_POST
def update_quick_note(request, note_id):
    """
    JSON endpoint to update an existing quick note.
    """
    note = get_object_or_404(QuickNote, id=note_id, user=request.user)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido.'}, status=400)

    title = data.get('title', note.title)
    content = data.get('content')
    referenced_event_id = data.get('referenced_event_id')

    if not content:
        return JsonResponse({'status': 'error', 'message': 'Conteúdo da nota é obrigatório.'}, status=400)

    referenced_event = None
    if referenced_event_id:
        try:
            referenced_event = Event.objects.get(id=referenced_event_id)
        except Event.DoesNotExist:
            pass

    note.title = title
    note.content = content
    note.referenced_event = referenced_event
    note.save()

    return JsonResponse({
        'status': 'success',
        'message': 'Nota atualizada!',
        'note': {
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'created_at': note.created_at.strftime('%d/%m/%Y %H:%M'),
            'referenced_event': {
                'id': note.referenced_event.id,
                'title': note.referenced_event.title,
                'color': note.referenced_event.color or '#3b82f6'
            } if note.referenced_event else None
        }
    })


@login_required
@require_module('agenda')
@require_POST
def create_location(request):
    """
    API endpoint to dynamically register a new physical location/space.
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'status': 'error', 'message': 'Dados inválidos.'}, status=400)

    if not name:
        return JsonResponse({'status': 'error', 'message': 'O nome do espaço é obrigatório.'}, status=400)

    # Check if a location with the same name already exists
    exists = Location.objects.filter(name__iexact=name).first()
    if exists:
        return JsonResponse({
            'status': 'success',
            'message': 'Este espaço já existe.',
            'location': {'id': exists.id, 'name': exists.name}
        })

    # Create new physical location/space
    location = Location.objects.create(name=name, is_meeting_room=True)
    return JsonResponse({
        'status': 'success',
        'message': 'Espaço cadastrado com sucesso!',
        'location': {'id': location.id, 'name': location.name}
    })


@login_required
@require_module('agenda')
@require_POST
def create_event_type(request):
    """
    API endpoint to dynamically register a new meeting/commitment type and its color.
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        color = data.get('color', '#3b82f6').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'status': 'error', 'message': 'Dados inválidos.'}, status=400)

    if not name:
        return JsonResponse({'status': 'error', 'message': 'O nome do tipo de compromisso é obrigatório.'}, status=400)

    # Check if type with the same name already exists
    exists = EventType.objects.filter(name__iexact=name).first()
    if exists:
        return JsonResponse({
            'status': 'success',
            'message': 'Este tipo de compromisso já existe.',
            'event_type': {'name': exists.name.lower(), 'label': exists.name, 'color': exists.color}
        })

    # Create new event type
    event_type = EventType.objects.create(name=name, color=color)
    return JsonResponse({
        'status': 'success',
        'message': 'Tipo de compromisso cadastrado com sucesso!',
        'event_type': {'name': event_type.name.lower(), 'label': event_type.name, 'color': event_type.color}
    })


@login_required
@require_module('agenda')
def manage_locations(request):
    """
    Renders and manages physical corporate spaces (Locations/Salas) in a premium card-based layout.
    Supports dynamic Listing, Creating, Editing, and Deleting spaces.
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        space_id = request.POST.get('id')
        name = request.POST.get('name', '').strip()
        capacity_str = request.POST.get('capacity', '10')
        note = request.POST.get('note', '').strip()

        try:
            capacity = int(capacity_str) if capacity_str else 10
        except ValueError:
            capacity = 10

        if action == 'create':
            if not name:
                return JsonResponse({'status': 'error', 'message': 'O nome do espaço é obrigatório.'})
            Location.objects.create(name=name, capacity=capacity, note=note, is_meeting_room=True)
            return JsonResponse({'status': 'success', 'message': 'Espaço criado com sucesso!'})

        elif action == 'update':
            space = get_object_or_404(Location, id=space_id)
            if not name:
                return JsonResponse({'status': 'error', 'message': 'O nome do espaço é obrigatório.'})
            space.name = name
            space.capacity = capacity
            space.note = note
            space.save()
            return JsonResponse({'status': 'success', 'message': 'Espaço atualizado com sucesso!'})

        elif action == 'delete':
            space = get_object_or_404(Location, id=space_id)
            space.delete()
            return JsonResponse({'status': 'success', 'message': 'Espaço excluído com sucesso!'})

        return JsonResponse({'status': 'error', 'message': 'Ação inválida.'})

    # GET request
    spaces = Location.objects.all().order_by('name')
    context = {
        'spaces': spaces,
    }
    return render(request, 'agenda/rooms_list.html', context)


@login_required
@require_module('agenda')
def manage_event_types(request):
    """
    Renders and manages meeting/commitment categories (Tipos de Compromisso) in a premium card-based layout.
    Supports dynamic Listing, Creating, Editing, and Deleting categories.
    """
    # Seed default EventType if none exist
    if not EventType.objects.exists():
        default_types = [
            ('Reunião', '#3b82f6'),
            ('Integração', '#10b981'),
            ('Entrevista', '#f59e0b'),
            ('Treinamento', '#8b5cf6'),
            ('Visita Técnica', '#ef4444'),
            ('Outro', '#64748b'),
        ]
        for name, color in default_types:
            EventType.objects.create(name=name, color=color)

    if request.method == 'POST':
        action = request.POST.get('action')
        type_id = request.POST.get('id')
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color', '#3b82f6').strip()

        if action == 'create':
            if not name:
                return JsonResponse({'status': 'error', 'message': 'O nome do tipo é obrigatório.'})
            if EventType.objects.filter(name__iexact=name).exists():
                return JsonResponse({'status': 'error', 'message': 'Já existe um tipo de reunião com este nome.'})
            EventType.objects.create(name=name, color=color)
            return JsonResponse({'status': 'success', 'message': 'Tipo de compromisso criado com sucesso!'})

        elif action == 'update':
            event_type = get_object_or_404(EventType, id=type_id)
            if not name:
                return JsonResponse({'status': 'error', 'message': 'O nome do tipo é obrigatório.'})
            if EventType.objects.filter(name__iexact=name).exclude(id=type_id).exists():
                return JsonResponse({'status': 'error', 'message': 'Já existe um tipo de reunião com este nome.'})
            event_type.name = name
            event_type.color = color
            event_type.save()
            return JsonResponse({'status': 'success', 'message': 'Tipo de compromisso atualizado com sucesso!'})

        elif action == 'delete':
            event_type = get_object_or_404(EventType, id=type_id)
            event_type.delete()
            return JsonResponse({'status': 'success', 'message': 'Tipo de compromisso excluído com sucesso!'})

        return JsonResponse({'status': 'error', 'message': 'Ação inválida.'})

    # GET request
    event_types = EventType.objects.all().order_by('name')
    context = {
        'event_types': event_types,
    }
    return render(request, 'agenda/event_types_list.html', context)


@login_required
@require_module('agenda')
def manage_quick_notes(request):
    """
    Renders a dedicated full-screen Google Keep/Pinterest style notes dashboard.
    Allows easy search, tagging, and deep linking back to calendar appointments.
    """
    quick_notes = QuickNote.objects.filter(user=request.user).select_related('referenced_event')
    open_events = Event.objects.filter(status__in=['aberto', 'agendado']).order_by('-start_date')
    

@login_required
@require_module('agenda')
def export_event_ics(request, event_id):
    """
    Gera e retorna um arquivo .ICS para o evento especificado.
    Compatível com Google Calendar, Outlook e Apple Calendar.
    """
    from django.utils import timezone as tz
    event = get_object_or_404(Event, id=event_id)

    def fmt_dt(dt):
        """Formata datetime para o padrão iCalendar (UTC)."""
        if dt.tzinfo is None:
            import pytz
            dt = pytz.timezone('America/Sao_Paulo').localize(dt)
        return dt.astimezone(pytz.utc).strftime('%Y%m%dT%H%M%SZ')

    try:
        import pytz
        dtstart = fmt_dt(event.start_date)
        dtend = fmt_dt(event.end_date)
        dtstamp = fmt_dt(tz.now())
    except Exception:
        dtstart = event.start_date.strftime('%Y%m%dT%H%M%S')
        dtend = event.end_date.strftime('%Y%m%dT%H%M%S')
        dtstamp = dtstart

    organizer_name = f"{event.organizer.first_name} {event.organizer.last_name}" if event.organizer else "Netline RH"
    location_parts = []
    if event.location:
        location_parts.append(event.location.name)
    if event.city:
        location_parts.append(event.city.name)
    location_str = ', '.join(location_parts)

    summary = event.title.replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')
    description = (event.notes or '').replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Netline RH//Agenda Corporativa//PT",
        "CALSCALE:GREGORIAN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:{event.id}@netlinerh.com.br",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}" if description else "",
        f"LOCATION:{location_str}" if location_str else "",
        f"URL:{event.meeting_link}" if event.meeting_link else "",
        f"ORGANIZER;CN={organizer_name}:MAILTO:{event.organizer.work_email or 'rh@netlinerh.com.br'}" if event.organizer else "",
        "STATUS:CONFIRMED",
        "END:VEVENT",
        "END:VCALENDAR",
    ]

    ics_content = "\r\n".join(line for line in lines if line)

    response = HttpResponse(ics_content, content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="compromisso-{event.id}.ics"'
    return response


@login_required
@require_module('agenda')
@require_POST
def cancel_event(request, event_id):
    """
    Cancela um evento da agenda, registra o motivo e envia email a todos os participantes.
    Apenas o organizador ou admin/HR pode cancelar.
    """
    event = get_object_or_404(Event, id=event_id)

    user = request.user
    is_organizer = event.organizer and event.organizer == getattr(user, 'employee', None)
    if not (is_organizer or getattr(user, 'is_admin', False) or getattr(user, 'is_hr', False) or user.is_superuser):
        return JsonResponse({'error': 'Sem permissao para cancelar este evento.'}, status=403)

    if event.status == 'cancelado':
        return JsonResponse({'error': 'Evento ja esta cancelado.'}, status=400)

    data = json.loads(request.body)
    reason = data.get('reason', '').strip()
    if not reason:
        return JsonResponse({'error': 'Informe o motivo do cancelamento.'}, status=400)

    event.status = 'cancelado'
    event.cancellation_reason = reason
    event.save()

    try:
        from attendance.google_sync import sync_corporate_event_to_google
        sync_corporate_event_to_google(event)
    except Exception:
        pass

    emails_to_notify = []
    for emp in event.employees.all():
        if emp.work_email:
            emails_to_notify.append(emp.work_email)
    if event.external_participants:
        import re
        for e in re.split(r'[;,\s\n\r]+', event.external_participants):
            e = e.strip()
            if e and '@' in e:
                emails_to_notify.append(e)

    if emails_to_notify:
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            from django.utils.timezone import localtime
            start_fmt = localtime(event.start_date).strftime('%d/%m/%Y %H:%M')
            subject = f"[CANCELADO] {event.title}"
            body = (
                f"Ola,\n\n"
                f"O evento '{event.title}' agendado para {start_fmt} foi CANCELADO.\n\n"
                f"Motivo: {reason}\n\n"
                f"Em caso de duvidas, entre em contato com o organizador.\n\n"
                f"-- Sistema NetlineRH"
            )
            from emails.utils import send_custom_email
            
            context = {
                'event_title': event.title,
                'start_time': start_fmt,
                'reason': reason
            }
            
            sent = send_custom_email('event_cancelled', context, emails_to_notify)
            if not sent:
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, emails_to_notify, fail_silently=True)
        except Exception:
            pass

    return JsonResponse({'success': True, 'message': 'Evento cancelado e participantes notificados.'})