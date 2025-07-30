import time
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.urls import reverse
from django.core.validators import MinLengthValidator
from django.utils.text import slugify
from django.db import transaction, IntegrityError
from django.db.models import F
import logging
from apps.sorteo.services import register_payment_api, get_payment_status_api
# Create your models here.
class Sorteo(models.Model):
    #TODO chequear por qué tickets_solds no está siendo calculado
    #TODO chequear percentage_sold después de ver por qué TICKETS_SOLDS no se ejecuta.
    ESTATE = [
        ('B', 'BORRADOR'),
        ('A', 'ACTIVO'),
        ('F', 'FINALIZADO'),
        ('V', 'VENDIDO')
    ]

    title = models.CharField(('Titulo'),max_length=50)
    slug = models.SlugField(unique=True, max_length=110, editable=False)
    description = models.TextField(('Descripción'))
    date_lottery = models.DateTimeField(("Fecha del Sorteo"), auto_now=False, auto_now_add=False)
    prize_picture = models.ImageField(("Foto del premio"), upload_to='premios/')
    ticket_price = models.DecimalField(("Precio del ticket"), max_digits=5, decimal_places=2)
    state = models.CharField(("Estado del sorteo"), choices=ESTATE, default='B', blank=False)
    total_tickets = models.PositiveIntegerField(("Máxima cantidad de tickets a vender"), blank=False)
    tickets_solds = models.PositiveIntegerField(("Tickets vendidos"), editable=False, default=0)
    is_main = models.BooleanField(("Sorteo Principal"), default=False, null=True)
    lottery_conditions = models.TextField(("Condiciones del sorteo"))

    class Meta:
        verbose_name = 'Sorteo'
        verbose_name_plural = 'Sorteos'
        ordering = ['-is_main','-date_lottery']

    
    def tickets_sold_quantity(self):
        self.tickets_solds = self.tickets.count()
        self.save(update_fields=['tickets_solds'])

    def percentage_sold(self):
        if self.total_tickets > 0:
            return (self.tickets_solds * 100) // self.total_tickets 
        return 0

    
    def get_absolute_url(self):
        return reverse('detalle_sorteo', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug =  slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Sorteo.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter} "
        
        if self.is_main:
            Sorteo.objects.filter(is_main = True).exclude(pk=self.pk).update(is_main=False)
        


        return super().save(*args, **kwargs)
    

   

class Ticket(models.Model):
    serial = models.PositiveIntegerField(("Número de ticket"))
    owner_name = models.CharField(("Nombre del propietario"), max_length=50)
    owner_ci = models.CharField(('Cedula del propietario'),max_length=8, validators=[MinLengthValidator(6)])
    owner_email = models.EmailField(("Correo del propietario"), max_length=254)
    owner_phone = PhoneNumberField(verbose_name='Telefono del propietario', region='VE')
    sorteo = models.ForeignKey("sorteo.sorteo", verbose_name="Sorteo", on_delete=models.CASCADE, related_name='tickets', null=False, blank=False)
    payment = models.ForeignKey("sorteo.payment", verbose_name="Pago", on_delete=models.CASCADE, related_name='tickets', null=False, blank=False)
    created_at = models.DateTimeField(("Fecha de Creación"), auto_now_add=True, editable=False)

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        unique_together = [['serial', 'sorteo']]
    
    def __str__(self):
        return f"Ticket #{self.serial} - {self.sorteo.title}"   
    
   

_logger = logging.getLogger(__name__)

class Payment(models.Model):
    #TODO signal para el update_at
    #TODO lógica para creación de tickets
    PAYMENT_METHODS = [
        ('P', 'Pago Móvil')
        ]
    PAYMENT_STATES =[
        ('V', 'Verificado'),
        ('E', 'En Espera'),
        ('C', 'Cancelado')
    ]

    CI_TYPE_CHOICES = [
        ('V', 'Venezolano'),
        ('E', 'Extranjero'),
        ('J', 'Jurídico'),
    ]
    BANK_CHOICES = [
        ('0102', 'Banco de Venezuela'),
        ('0104', 'Banco Venezolano de Crédito'),
        ('0105', 'Banco Mercantil'),
        ('0108', 'Banco Provincial'),
        ('0114', 'Bancaribe'),
        ('0115', 'Banco Exterior'),
        ('0128', 'Banco Caroní'),
        ('0134', 'Banesco'),
        ('0137', 'Banco Sofitasa'),
        ('0138', 'Banco Plaza'),
        ('0151', 'BFC Banco Fondo Común'),
        ('0156', '100% Banco'),
        ('0157', 'DelSur Banco Universal'),
        ('0163', 'Banco del Tesoro'),
        ('0166', 'Banco Agrícola de Venezuela'),
        ('0168', 'Bancrecer'),
        ('0169', 'Mi Banco'),
        ('0171', 'Banco Activo'),
        ('0172', 'Bancamiga'),
        ('0174', 'Banplus'),
        ('0175', 'Banco Bicentenario del Pueblo'),
        ('0177', 'Banfanb'),
        ('0191', 'BNC Banco Nacional de Crédito'),
    ]
    owner_name = models.CharField(("Nombre del propietario"), max_length=50)
    owner_ci = models.CharField(('Cedula del propietario'),max_length=8, validators=[MinLengthValidator(6)])
    owner_email = models.EmailField(("Correo del propietario"), max_length=254)
    owner_phone = PhoneNumberField(verbose_name='Telefono del propietario', region='VE')
    method = models.CharField(("Método de Pago"), max_length=50, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=30)
    state = models.CharField(("Estado"), max_length=50, choices=PAYMENT_STATES)
    created_at = models.DateTimeField(("Fecha de creación"), auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(("Ultima actualización"), auto_now=False, null=True, editable=False)
    tickets_quantity = models.PositiveBigIntegerField()
    serial = models.CharField(("Serial de la transacción"), max_length=50, editable=False, blank=True)
    sorteo = models.ForeignKey('Sorteo', on_delete=models.CASCADE, related_name='pagos')
    transferred_amount = models.DecimalField(("Monto transferido"), max_digits=10, decimal_places=2)
    transferred_date = models.DateField(("Fecha de transferencia"), auto_now=False, auto_now_add=False)
    type_CI = models.CharField(("Tipo de cédula"), max_length=1, choices=CI_TYPE_CHOICES, default='V')
    bank_of_transfer = models.CharField(("Banco de transferencia"), max_length=4, choices=BANK_CHOICES)
    payment_verification_note = models.TextField(("Nota de verificación del pago"), blank=True, null=True)
    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago {self.id} - {self.owner_name}"

    def save(self, *args, **kwargs):
        if not self.serial:
            self.serial = f"REF-{self.owner_ci[:4]}-{int(time.time())}"
        
        is_new = self.pk is None
        old_state = None
        if not is_new:
            # Obtenemos solo el estado para evitar una consulta completa si no es necesaria
            old_state = Payment.objects.values_list('state', flat=True).get(pk=self.pk)

        super().save(*args, **kwargs)

    def process_verified_payment(self):
        """
        Registra el pago en la API externa y, si es aprobado, crea los tickets y actualiza el contador del sorteo.
        """
        try:
            # Registrar el pago en la API externa
            success, response = register_payment_api(self)
    
            if not success:
                # Si la API devuelve un error, marcar el pago como "En Espera" y registrar el error
                self.state = 'E'  # En Espera
                self.save(update_fields=['state'])
                _logger.error(f"Error al registrar el pago {self.id} en la API: {response.get('descripcion')}")
                return False
    
            # Procesar la respuesta de la API
            codigo_respuesta = response.get("codigo_respuesta")
            descripcion = response.get("descripcion")
            _logger.info(f"Respuesta de la API para el pago {self.id}: {codigo_respuesta} - {descripcion}")
    
            if codigo_respuesta in ["PAGO_INGRESADO", "IDPAGO_YA_REGISTRADO"]:
                # Si el pago fue ingresado correctamente, verificar su estado
                status_response = get_payment_status_api(self)
                status_codigo = status_response.get("codigo_respuesta")
                status_descripcion = status_response.get("descripcion")
    
                if status_codigo == "OK":
                    estatus = status_response.get("codigo_respuesta")
                    if estatus == "APROBADO":
                        # Crear los tickets si el pago es aprobado
                        with transaction.atomic():
                            sorteo = Sorteo.objects.select_for_update().get(pk=self.sorteo.pk)
    
                            # Validar que haya suficientes boletos disponibles
                            if (sorteo.tickets_solds + self.tickets_quantity) > sorteo.total_tickets:
                                self.state = 'C'  # Cancelado
                                self.save(update_fields=['state'])
                                return False
    
                            last_ticket = sorteo.tickets.order_by('-serial').first()
                            start_serial = (last_ticket.serial + 1) if last_ticket else 1
    
                            # Crear los boletos en lote
                            tickets_to_create = [
                                Ticket(
                                    serial=start_serial + i,
                                    owner_name=self.owner_name,
                                    owner_ci=self.owner_ci,
                                    owner_email=self.owner_email,
                                    owner_phone=self.owner_phone,
                                    sorteo=sorteo,
                                    payment=self
                                ) for i in range(self.tickets_quantity)
                            ]
                            Ticket.objects.bulk_create(tickets_to_create)
    
                            # Actualizar el contador de boletos vendidos
                            sorteo.tickets_solds = F('tickets_solds') + self.tickets_quantity
                            sorteo.save(update_fields=['tickets_solds'])
    
                            # Marcar el pago como verificado
                            self.state = 'V'
                            self.save(update_fields=['state'])
                            _logger.info(f"Pago {self.id} verificado. {self.tickets_quantity} boletos creados para el sorteo {sorteo.id}.")
                            return True
    
                    elif estatus == "RECHAZADO":
                        # Si el pago es rechazado, marcarlo como cancelado
                        self.state = 'C'  # Cancelado
                        self.save(update_fields=['state'])
                        _logger.warning(f"Pago {self.id} rechazado: {status_descripcion}")
                        return False
    
                    elif estatus == "EN PROCESO":
                        # Si el pago está en proceso, dejarlo en estado "En Espera"
                        self.state = 'E'  # En Espera
                        self.save(update_fields=['state'])
                        _logger.info(f"Pago {self.id} en proceso de verificación: {status_descripcion}")
                        return False
    
                else:
                    # Si la verificación falla, marcar el pago como "En Espera"
                    self.state = 'E'  # En Espera
                    self.save(update_fields=['state'])
                    _logger.error(f"Error al verificar el estado del pago {self.id}: {status_descripcion}")
                    return False
            elif codigo_respuesta in ["TRANSFERENCIA_YA_REGISTRADA"]:
                # Si la transferencia ya fue registrada, marcar el pago como cancelada
                self.state = 'C'
                self.payment_verification_note = f'Pago cancelado: {status_descripcion}'
            
            else:
                # Si la API devuelve un error al registrar el pago, marcarlo como "En Espera"
                self.state = 'E'  # En Espera
                self.save(update_fields=['state'])
                _logger.error(f"Error al registrar el pago {self.id}: {descripcion}")
                return False
    
        except Exception as e:
            _logger.error(f"Error inesperado al procesar el pago {self.id}: {e}")
            return False
    
    