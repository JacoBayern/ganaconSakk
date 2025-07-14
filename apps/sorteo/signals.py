from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Ticket

@receiver([post_save, post_delete], sender=Ticket)
def update_tickets_sold(sender, instance, **kwargs):
    sorteo = instance.sorteo
    sorteo.tickets_solds = sorteo.tickets.count()  
    sorteo.save(update_fields=['tickets_solds']) 

