from django.contrib import admin
from .models import Ticket, Sorteo, Payment

# Register your models here.
admin.site.register(Ticket)
admin.site.register(Sorteo)
admin.site.register(Payment)
