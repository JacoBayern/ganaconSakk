import time
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.urls import reverse
from django.core.validators import MinLengthValidator
from django.utils.text import slugify
from django.db import transaction, IntegrityError
from django.db.models import F
import logging
import random
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
    winner_picture = models.ImageField(("Foto del ganador"), upload_to='ganadores/', null=True, blank=True)
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

    def __str__(self):
        return self.title

    
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
        ('P', 'Pago Móvil'),
        ('Z', 'Zelle')
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
    reference = models.CharField( ("Referencia del pago"),max_length=30)
    state = models.CharField(("Estado"), max_length=50, choices=PAYMENT_STATES)
    created_at = models.DateTimeField(("Fecha de creación"), auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(("Ultima actualización"), auto_now=False, null=True, editable=False)
    tickets_quantity = models.PositiveBigIntegerField(("Cantidad de tickets"))
    serial = models.CharField(("Serial de la transacción"), max_length=50, editable=False, blank=True)
    sorteo = models.ForeignKey('Sorteo', on_delete=models.CASCADE, related_name='pagos')
    transferred_amount = models.DecimalField(("Monto transferido"), max_digits=10, decimal_places=2)
    transferred_date = models.DateField(("Fecha de transferencia"), auto_now=False, auto_now_add=False)
    type_CI = models.CharField(("Tipo de cédula"), max_length=1, choices=CI_TYPE_CHOICES, default='V')
    bank_of_transfer = models.CharField(("Banco de transferencia"), max_length=4, choices=BANK_CHOICES)
    payment_verification_note = models.TextField(("Nota de verificación del pago"), blank=True, null=True)
    is_payment_registered = models.BooleanField(("Pago registrado"), default=False, editable=False)
    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago {self.id} - {self.owner_name}"

    def save(self, *args, **kwargs):
        if not self.serial:
            self.serial = f"REF-{self.owner_ci[:4]}-{int(time.time())}"

        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new and self.method == 'Z':
            if not self.create_tickets():
                _logger.error(f"La creación de tickets manual para el pago {self.id} falló.")

    def process_verified_payment(self):
        """
        Registra el pago en la API externa y, si es aprobado, crea los tickets y actualiza el contador del sorteo.
        """
        try:
            # Registrar el pago en la API externa
            if not self.is_payment_registered:
                success, response = register_payment_api(self)
                if not success:
                    # Si la API devuelve un error, marcar el pago como "En Espera" y registrar el error
                    self.state = 'E'  # En Espera
                    self.payment_verification_note = f"Error al registrar el pago: {response.get('descripcion')}"
                    self.save(update_fields=['state', 'payment_verification_note'])
                    _logger.error(f"Error al registrar el pago {self.id} en la API: {response.get('descripcion')}")
                    return False, response.get('descripcion')

            # Procesar la respuesta de la API
            codigo_respuesta = response.get("codigo_respuesta")
            descripcion = response.get("descripcion")
            _logger.info(f"Respuesta de la API para el pago {self.id}: {codigo_respuesta} - {descripcion}")
            if codigo_respuesta in ["PAGO_INGRESADO", "IDPAGO_YA_REGISTRADO"]:
                # Si el pago fue ingresado correctamente, verificar su estado
                self.is_payment_registered = True
                _logger.warning('HOLAAAAAA ENTRÉ ACÁ')
                self.save(update_fields=['is_payment_registered'])
                _logger.warning('HOLAAAAAA ENTRÉ ACÁ OTRAVEEEEEE')
                status_response = get_payment_status_api(self)
                status_codigo = status_response.get("codigo_respuesta")
                status_descripcion = status_response.get("descripcion")
                _logger.warning(f'STATUUUUUUUUUUUS: {status_codigo}')
                estatus = status_response.get("estatus")
                _logger.warning(f'ESTATUS: {estatus}')
                if status_codigo == "OK":
                    if estatus == "APROBADO":
                        self.create_tickets()
                        return True, "Pago aprobado y boletos creados exitosamente."
                    elif estatus == "RECHAZADO":
                        # Si el pago es rechazado, marcarlo como cancelado
                        self.state = 'C'  # Cancelado
                        self.payment_verification_note = f"Pago rechazado: {status_descripcion}"
                        self.save(update_fields=['state', 'payment_verification_note'])
                        _logger.warning(f"Pago {self.id} rechazado: {status_descripcion}")
                        return False, status_descripcion
                    elif estatus == "EN PROCESO":
                        # Si el pago está en proceso, dejarlo en estado "En Espera"
                        self.state = 'E'  # En Espera
                        self.payment_verification_note = f"Pago En proceso de verificación: {status_descripcion}"
                        self.save(update_fields=['state', 'payment_verification_note'])
                        _logger.info(f"Pago {self.id} en proceso de verificación: {status_descripcion}")
                        return True, status_descripcion
                elif status_codigo == 'ID_PAGO_NO_REGISTRADO':
                    self.state = 'E'  # En Espera
                    self.payment_verification_note = f"Pago no registrado: {status_descripcion}"
                    self.save(update_fields=['state', 'payment_verification_note'])
                    _logger.error(f"Pago no registrado {self.id}: {status_descripcion}")
                    return False, 'Error al verificar el pago: Contacte a soporte'
                elif status_codigo == 'USUARIO_NO_VALIDO':
                    self.state = 'E'  # En Espera
                    self.payment_verification_note = f"Usuario no válido: {status_descripcion}"
                    self.save(update_fields=['state', 'payment_verification_note'])
                    _logger.error(f"Pago no registrado {self.id}: {status_descripcion}")
                    return False, 'Error al verificar el pago: Contacte a soporte'

            elif codigo_respuesta in ['ERROR_INTERNO']:
                self.state = 'E'  # En Espera
                self.payment_verification_note = f"Error interno al verificar el pago: En unos momentos se intentará de nuevo. Puede cerrar esta pestaña"
                self.save(update_fields=['state', 'payment_verification_note'])
                return False, "Error interno al verificar el pago."
            elif codigo_respuesta in ["TRANSFERENCIA_YA_REGISTRADA"]:
                # Si la transferencia ya fue registrada, marcar el pago como cancelada
                self.state = 'C'
                self.payment_verification_note = f'Pago cancelado: {descripcion}'
                self.save(update_fields=['state', 'payment_verification_note'])
                _logger.error(f"Pago ya registrado {self.id}: {descripcion}")
                return False, 'Pago ya registrado, por favor verifique su número de referencia.'
            else:
                self.state = 'C'  # Cancelado
                self.payment_verification_note = f"Error al verificar el pago: {descripcion}"
                self.save(update_fields=['state', 'payment_verification_note'])
                _logger.error(f"Error al registrar el pago {self.id}: {descripcion}")
                return False, descripcion
        except Exception as e:
            _logger.error(f"Error inesperado al procesar el pago {self.id}: {e}")
            return False, "Error inesperado al procesar el pago."
        return False, codigo_respuesta
    
    
    def create_tickets(self):
        """Crea tickets para un pago aprobado de manera atómica"""
        _logger.info(f'Iniciando creación de tickets para pago {self.id}')
        tickets_to_generate = self.tickets_quantity

        try:
            with transaction.atomic():
                sorteo = Sorteo.objects.select_for_update().get(pk=self.sorteo.pk)

                # Validar disponibilidad
                if (sorteo.tickets_solds + tickets_to_generate) > sorteo.total_tickets:
                    self.state = 'C'  # Cancelado
                    self.save(update_fields=['state'])
                    _logger.warning(f'No hay tickets disponibles. Pago {self.id} cancelado')
                    return False

                existing_serials = set(Ticket.objects.filter(sorteo=sorteo).values_list('serial', flat=True))
                generated_serials = set()
                max_attempts = sorteo.total_tickets * 2  # Límite para evitar loops infinitos
                attempts = 0

                # Generación de números únicos
                while len(generated_serials) < tickets_to_generate and attempts < max_attempts:
                    potential_serial = random.randint(1, sorteo.total_tickets)
                    if potential_serial not in existing_serials and potential_serial not in generated_serials:
                        generated_serials.add(potential_serial)
                    attempts += 1

                if len(generated_serials) < tickets_to_generate:
                    raise ValueError("No se pudieron generar números de tickets únicos")

                tickets_to_create = [
                    Ticket(
                        serial=serial,
                        owner_name=self.owner_name,
                        owner_ci=self.owner_ci,
                        owner_email=self.owner_email,
                        owner_phone=self.owner_phone,
                        sorteo=sorteo,
                        payment=self
                    ) 
                    for serial in generated_serials
                ]

                Ticket.objects.bulk_create(tickets_to_create)
                _logger.warning(f'TICKETS CREADOOOOS{tickets_to_create}')
                _logger.info(f'Creados {len(tickets_to_create)} tickets para pago {self.id}')

                # Actualizar contador
                sorteo.tickets_solds = F('tickets_solds') + tickets_to_generate
                sorteo.save(update_fields=['tickets_solds'])

                # Actualizar estado del pago
                self.state = 'V'
                self.payment_verification_note = (
                    f"Pago verificado y {tickets_to_generate} boletos creados "
                    f"para el sorteo {sorteo.title}."
                )
                self.save(update_fields=['state', 'payment_verification_note'])

                return True

        except Exception as e:
            _logger.error(f"Error crítico al crear tickets para pago {self.id}: {str(e)}", 
                         exc_info=True)
            raise  # Re-lanza la excepción para manejo superior