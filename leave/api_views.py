from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date
from datetime import datetime, date

from .models import LeaveRequest, LeaveType, Holiday

class LeaveCalendarAPIView(APIView):
    """
    Retorna Feriados e Ausências (LeaveRequests) do usuário logado
    para alimentar o calendário do aplicativo.
    GET /api/v1/leave/calendar/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = request.user.employee

        
        
        leaves = LeaveRequest.objects.filter(
            employee=employee,
        ).exclude(
            status__in=[LeaveRequest.STATUS_CANCELLED, LeaveRequest.STATUS_REJECTED]
        ).select_related('leave_type')

        leave_data = []
        for l in leaves:
            leave_data.append({
                'id': l.id,
                'type': l.leave_type.name,
                'from_date': str(l.from_date),
                'to_date': str(l.to_date),
                'status': l.status,
                'status_display': l.get_status_display(),
                'comment': l.comment,
            })

        
        current_year = date.today().year
        holidays = Holiday.objects.filter(date__year__gte=current_year - 1)
        
        holiday_data = []
        for h in holidays:
            holiday_data.append({
                'id': h.id,
                'name': h.name,
                'date': str(h.date),
                'length': h.length, 
                'recurring': h.recurring,
            })

        return Response({
            'leaves': leave_data,
            'holidays': holiday_data,
        })


class LeaveTypeAPIView(APIView):
    """
    Retorna os tipos de licença disponíveis para preencher o formulário
    GET /api/v1/leave/types/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        types = LeaveType.objects.filter(is_deleted=False)
        data = [{'id': t.id, 'name': t.name, 'default_days': t.default_days} for t in types]
        return Response(data)


class LeaveRequestCreateAPIView(APIView):
    """
    Cria uma nova solicitação de licença/ausência
    POST /api/v1/leave/add/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        try:
            employee = request.user.employee
        except Exception:
            return Response({"error": "Perfil de funcionário não encontrado."}, status=status.HTTP_400_BAD_REQUEST)

        leave_type_id = request.data.get('leave_type_id')
        from_date_str = request.data.get('from_date')
        to_date_str = request.data.get('to_date')
        comment = request.data.get('comment', '')
        attachment = request.FILES.get('attachment')  

        if not leave_type_id or not from_date_str or not to_date_str:
            return Response(
                {"error": "Tipo de licença, data de início e data de fim são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            leave_type = LeaveType.objects.get(id=leave_type_id, is_deleted=False)
        except LeaveType.DoesNotExist:
            return Response({"error": "Tipo de licença inválido."}, status=status.HTTP_400_BAD_REQUEST)

        from_date = parse_date(from_date_str)
        to_date = parse_date(to_date_str)

        if not from_date or not to_date:
            return Response({"error": "Formato de data inválido. Use AAAA-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        if from_date > to_date:
            return Response({"error": "A data inicial não pode ser depois da data final."}, status=status.HTTP_400_BAD_REQUEST)

        
        leave_name = leave_type.name.lower()
        is_folga = 'folga' in leave_name
        
        if not is_folga and not attachment:
            return Response(
                {"error": f'O tipo de licença "{leave_type.name}" exige um atestado/documento anexado.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        
        leave_request = LeaveRequest.objects.create(
            employee=employee,
            leave_type=leave_type,
            from_date=from_date,
            to_date=to_date,
            comment=comment,
            attachment=attachment,
            status=LeaveRequest.STATUS_PENDING
        )

        return Response(
            {"message": "Solicitação criada com sucesso!", "id": leave_request.id},
            status=status.HTTP_201_CREATED
        )

