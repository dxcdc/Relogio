from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Payslip

class PayslipListAPIView(APIView):
    """
    Retorna a lista de holerites do funcionário logado
    GET /api/v1/payroll/payslips/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            employee = request.user.employee
        except Exception:
            return Response({"error": "Perfil de funcionário não encontrado."}, status=status.HTTP_400_BAD_REQUEST)

        
        payslips = Payslip.objects.filter(employee=employee).order_by('-reference_year', '-reference_month')
        
        payslip_data = []
        for p in payslips:
            payslip_data.append({
                'id': p.id,
                'title': f"Holerite - {p.reference_month:02d}/{p.reference_year}",
                'date': f"{p.reference_month:02d}/{p.reference_year}",
                'status': p.status.lower(),
                'status_display': p.get_status_display(),
                'document_url': request.build_absolute_uri(p.document.url) if p.document else None,
                'requires_signature': True,
                'is_signed': p.status == Payslip.STATUS_SIGNED,
                'signed_at': p.signed_at,
                'signed_ip': p.signed_ip,
                'signature_hash': p.signature_hash,
            })

        return Response(payslip_data, status=status.HTTP_200_OK)


class PayslipSignAPIView(APIView):
    """
    Processa a assinatura digital do holerite vindo do aplicativo Flutter
    POST /api/v1/payroll/payslips/<id>/sign/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            payslip = Payslip.objects.get(pk=pk)
        except Payslip.DoesNotExist:
            return Response({"error": "Holerite não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
        
        if getattr(request.user, 'employee', None) != payslip.employee:
            return Response({"error": "Acesso negado."}, status=status.HTTP_403_FORBIDDEN)
            
        if payslip.status == Payslip.STATUS_SIGNED:
            return Response({"error": "Este holerite já foi assinado."}, status=status.HTTP_400_BAD_REQUEST)

        password = request.data.get('password')
        signature_image = request.data.get('signature_image')

        if not password or not signature_image:
            return Response(
                {"error": "Senha e imagem da assinatura (Base64) são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.check_password(password):
            return Response({"error": "Senha incorreta."}, status=status.HTTP_401_UNAUTHORIZED)
            
        if not signature_image.startswith('data:image'):
            return Response(
                {"error": "O formato da imagem da assinatura deve ser Base64 válido (data:image/png;base64,...)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')

        success = payslip.sign_document(ip_address=ip, signature_base64=signature_image)
        
        if success:
            return Response({
                "message": "Holerite assinado digitalmente com sucesso!",
                "status": payslip.status,
                "signed_at": payslip.signed_at,
                "signature_hash": payslip.signature_hash,
                "document_url": request.build_absolute_uri(payslip.document.url) if payslip.document else None
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Falha ao aplicar o carimbo digital no documento."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
