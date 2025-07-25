import time
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.urls import reverse
from django.core.validators import MinLengthValidator
from django.utils.text import slugify
from django.db import transaction, IntegrityError
from django.db.models import F
import logging
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
        return (self.tickets_solds * 100) // self.total_tickets 
        

    
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
    owner_name = models.CharField(("Nombre del propietario"), max_length=50)
    owner_ci = models.CharField(('Cedula del propietario'),max_length=8, validators=[MinLengthValidator(6)])
    owner_email = models.EmailField(("Correo del propietario"), max_length=254)
    owner_phone = PhoneNumberField(verbose_name='Telefono del propietario', region='VE')
    method = models.CharField(("Método de Pago"), max_length=50, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=30)
    state = models.CharField(("Estado"), max_length=50, choices=PAYMENT_STATES)
    created_at = models.DateTimeField(("Fecha de Pago"), auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(("Ultima actualización"), auto_now=False, null=True, editable=False)
    tickets_quantity = models.PositiveBigIntegerField()
    serial = models.CharField(("Serial de la transacción"), max_length=50, editable=False, blank=True)
    sorteo = models.ForeignKey('Sorteo', on_delete=models.CASCADE, related_name='pagos')
    transferred_amount = models.DecimalField(("Monto transferido"), max_digits=10, decimal_places=2)
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

        # --- Lógica de Verificación ---
        # Se ejecuta solo si el estado ha cambiado a 'Verificado'
        if not is_new and old_state != 'V' and self.state == 'V':
            self.process_verified_payment()

    def process_verified_payment(self):
        """
        Crea los tickets y actualiza el contador del sorteo de forma atómica.
        Se ejecuta cuando un pago es verificado.
        """
        try:
            with transaction.atomic():
                # 1. Bloquear el sorteo para evitar race conditions y obtener el estado más reciente.
                sorteo = Sorteo.objects.select_for_update().get(pk=self.sorteo.pk)

                # 2. Validar que haya suficientes boletos disponibles.
                if (sorteo.tickets_solds + self.tickets_quantity) > sorteo.total_tickets:
                    self.state = 'C' # Marcar como Cancelado
                    self.save(update_fields=['state']) # Usar update_fields para evitar recursión.
                    return

                last_ticket = sorteo.tickets.order_by('-serial').first()
                start_serial = (last_ticket.serial + 1) if last_ticket else 1

                # 4. Preparar los boletos para la creación en lote.
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
                
                # 5. Crear los boletos en una sola consulta (muy eficiente).
                Ticket.objects.bulk_create(tickets_to_create)

                # 6. Actualizar el contador de boletos vendidos en el sorteo de forma atómica.
                sorteo.tickets_solds = F('tickets_solds') + self.tickets_quantity
                sorteo.save(update_fields=['tickets_solds'])
                payment = Payment.objects.select_for_update().get(pk=self.pk)
                payment.state = 'V'
                payment.save(update_fields=['state'])
                _logger.info(f"Pago {self.id} verificado. {self.tickets_quantity} boletos creados para el sorteo {sorteo.id}.")

        except Exception as e:
            _logger.error(f"Error inesperado al procesar pago {self.id}: {e}")
            return False
        
        return True
   
