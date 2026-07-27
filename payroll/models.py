import hashlib
import os
from django.db import models
from django.utils import timezone
from pim.models import Employee

def payslip_document_path(instance, filename):
    nome_pasta = "desconhecido"
    if instance.employee:
        nome_pasta = instance.employee.full_name.replace(" ", "_").lower()
    return f'payslips/{nome_pasta}/{filename}'

class Payslip(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SIGNED = 'signed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Aguardando Assinatura'),
        (STATUS_SIGNED, 'Assinado'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    reference_month = models.IntegerField(verbose_name='Mês Referência')
    reference_year = models.IntegerField(verbose_name='Ano Referência')
    
    document = models.FileField(upload_to=payslip_document_path, null=True, blank=True, verbose_name='Arquivo PDF')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='Status')
    
    
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name='Data/Hora da Assinatura')
    signed_ip = models.CharField(max_length=45, null=True, blank=True, verbose_name='IP do Signatário')
    signature_hash = models.CharField(max_length=255, null=True, blank=True, verbose_name='Código Hash de Autenticidade')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Holerite'
        verbose_name_plural = 'Holerites'
        unique_together = ('employee', 'reference_month', 'reference_year')

    def __str__(self):
        return f"Holerite {self.reference_month:02d}/{self.reference_year} - {self.employee.full_name}"

    def sign_document(self, ip_address, signature_base64=None):
        if self.status != self.STATUS_PENDING:
            return False
            
        self.signed_at = timezone.now()
        self.signed_ip = ip_address
        self.status = self.STATUS_SIGNED
        
        file_hash = ''
        file_content = None
        
        # 1. Lê o arquivo de forma universal (funciona no Local, S3, Cloudinary, Google Drive...)
        if self.document:
            file_content = self.document.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
        
        raw_string = f"{self.employee.id}-{self.reference_month}-{self.reference_year}-{file_hash}-{self.signed_at.timestamp()}-{ip_address}"
        self.signature_hash = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()
        self.save()
        
        # 2. Injeta a assinatura trabalhando apenas na Memória RAM
        if file_content:
            try:
                import io
                from pypdf import PdfReader, PdfWriter
                from reportlab.pdfgen import canvas
                from reportlab.lib.colors import HexColor
                from django.utils.timezone import localtime
                from django.core.files.base import ContentFile

                packet = io.BytesIO()
                
                # Lê o PDF original direto da memória
                existing_pdf = PdfReader(io.BytesIO(file_content))
                output = PdfWriter()
                
                first_page = existing_pdf.pages[0]
                width = float(first_page.mediabox.width)
                height = float(first_page.mediabox.height)
                
                c = canvas.Canvas(packet, pagesize=(width, height))
                
                box_width = 240
                box_height = 130
                margin = 20
                
                x = width - box_width - margin
                y = margin
                
                c.setFillColor(HexColor("#ffffff"))
                c.setStrokeColor(HexColor("#10b981"))
                c.setLineWidth(1.5)
                c.rect(x, y, box_width, box_height, fill=1, stroke=1)

                c.setFillColor(HexColor("#10b981"))
                c.setFont("Helvetica-Bold", 10)
                c.drawCentredString(x + box_width/2, y + 112, "ASSINADO ELETRONICAMENTE")
                
                if signature_base64:
                    from reportlab.lib.utils import ImageReader
                    import base64
                    try:
                        header, encoded = signature_base64.split(",", 1)
                        data = base64.b64decode(encoded)
                        img = ImageReader(io.BytesIO(data))
                        c.drawImage(img, x + box_width/2 - 60, y + 60, width=120, height=45, mask='auto')
                    except Exception as e:
                        print("Erro ao processar imagem base64:", e)
                
                c.setFillColor(HexColor("#0f172a"))
                c.setFont("Helvetica-Bold", 8)
                c.drawCentredString(x + box_width/2, y + 48, f"Por: {self.employee.full_name}")
                
                c.setFont("Helvetica", 7)
                local_time = localtime(self.signed_at)
                time_str = local_time.strftime("%d/%m/%Y às %H:%M:%S")
                c.drawCentredString(x + box_width/2, y + 36, f"Data: {time_str} | IP: {self.signed_ip}")
                
                c.setFillColor(HexColor("#475569"))
                c.setFont("Courier", 6)
                c.drawCentredString(x + box_width/2, y + 22, "Hash de Autenticidade (SHA-256):")
                c.setFont("Courier-Bold", 5.5)
                
                hash_str = self.signature_hash
                c.drawCentredString(x + box_width/2, y + 12, hash_str[:32])
                c.drawCentredString(x + box_width/2, y + 5, hash_str[32:])

                c.save()
                packet.seek(0)
                stamp_pdf = PdfReader(packet)
                stamp_page = stamp_pdf.pages[0]
                
                for i, page in enumerate(existing_pdf.pages):
                    if i == 0:
                        page.merge_page(stamp_page)
                    output.add_page(page)
                    
                # Grava o resultado em um buffer de memória em vez de arquivo no HD
                final_pdf_io = io.BytesIO()
                output.write(final_pdf_io)
                
                # Opcional: deletar o antigo da nuvem antes de salvar (evita lixo de PDFs)
                old_name = self.document.name
                self.document.delete(save=False)
                
                # Salva o novo arquivo usando o mecanismo do Django (Storage Agnóstico)
                self.document.save(old_name, ContentFile(final_pdf_io.getvalue()), save=True)
                
            except Exception as e:
                print(f"Erro ao injetar assinatura: {e}")

        return True

from django.db.models.signals import post_save
from django.dispatch import receiver
from core.push_notifications import send_push

@receiver(post_save, sender=Payslip)
def notify_payslip_created(sender, instance, created, **kwargs):
    """Notifica o funcionário via Push Notification quando um novo holerite é enviado para assinatura."""
    if created and instance.status == Payslip.STATUS_PENDING:
        employee = instance.employee
        user = getattr(employee, 'user', None)
        if user and getattr(user, 'fcm_token', None):
            try:
                mes_ano = f"{instance.reference_month:02d}/{instance.reference_year}"
                send_push(
                    user,
                    "Holerite Disponível para Assinatura",
                    f"O seu holerite de {mes_ano} já está disponível. Por favor, acesse o app para assiná-lo.",
                    data={'route': '/documents/'}
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to send payslip push: {e}")
