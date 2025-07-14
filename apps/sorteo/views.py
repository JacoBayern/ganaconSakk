from django.shortcuts import render
from .models import Sorteo
import logging
_logger = logging.getLogger()

def home(request):
    sorteo_principal = Sorteo.objects.filter(is_main=True).first()
    otros_sorteos = Sorteo.objects.exclude(is_main=True).order_by('-date_lottery')[:6]
    porcentaje_vendido = sorteo_principal.percentage_sold()
    context ={
        'sorteo_principal': sorteo_principal,
        'otros_sorteos': otros_sorteos,
        'porcentaje_vendido': porcentaje_vendido
    }
    _logger.warning(otros_sorteos)
    return render(request, 'index.html', context)