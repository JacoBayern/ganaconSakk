from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Ticket

# @receiver([post_save, post_delete], sender=Ticket) # Desactivado
def update_tickets_sold(sender, instance, **kwargs):
    # Esta lógica ahora es manejada de forma más eficiente y segura
    # en el método Payment.save() y ya no es necesaria aquí.
    # Mantenerla causaría ineficiencias y posibles race conditions.
    pass
