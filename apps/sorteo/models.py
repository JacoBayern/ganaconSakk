from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.urls import reverse
from django.core.validators import MinLengthValidator
from django.utils.text import slugify
# Create your models here.
class Sorteo(models.Model):
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
    created_at = models.DateTimeField(("Fecha de Creación"), auto_now_add=True)
    
    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        unique_together = [['serial', 'sorteo']]
    
    def __str__(self):
        return f"Ticket #{self.serial} - {self.sorteo.title}"   
    
   

class Payment(models.Model):
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
    created_at = models.DateTimeField(("Fecha de Pago"), auto_now_add=True)
    updated_at = models.DateTimeField(("Ultima actualización"), auto_now=False)
    tickets_quantity = models.PositiveBigIntegerField()

    sorteo = models.ForeignKey('Sorteo', on_delete=models.CASCADE, related_name='pagos')
    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago {self.id} - {self.owner_name}"

   
