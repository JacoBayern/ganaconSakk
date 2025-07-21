from django.shortcuts import render, get_object_or_404
from .models import Sorteo, Payment
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .forms import PaymentForm
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

def details(request, sorteo_id):
    sorteo = get_object_or_404(Sorteo, pk=sorteo_id)
    porcentaje = sorteo.percentage_sold()
    form = PaymentForm()
    context = {
        'sorteo' : sorteo,
        'porcentaje': porcentaje,
        'form': form
    }
    return render(request, 'sorteo/detalles_sorteo.html', context)

#TODO añadir validación en caso de que el monto y la cantidad de boletos no coincidan con el calculo trayendo el objeto.
#TODO añadir validación en caso de que la rifa ya no esté disponible.
#TODO implementar API
@require_http_methods(["POST"])
def create_payment(request, sorteo_id):
    #TODO verificacion de numero telefonico
    #TODO verificacion de cédula de identidad
    try:
        sorteo = Sorteo.objects.get(pk=sorteo_id)
    except Sorteo.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Sorteo no disponible o no encontrado!'})

    form = PaymentForm(request.POST)
    #Check if the sorteo is available
    if sorteo.state != 'A':
        return JsonResponse({'status': 'error', 'message': 'El sorteo ya no está disponible!'}, status=400)

    #Check if the transferred amount matches the ticket price and quantity
    transferred_amount = float(form.data.get('transferred_amount'))
    if transferred_amount != sorteo.ticket_price * int(form.data.get('tickets_quantity')):
        return JsonResponse({'status': 'error', 'message': 'El monto transferido no coincide con el precio de los boletos!'}, status=400)
    
    #Check if theres another payment with the same reference
    reference = form.data.get('reference')
    if Payment.objects.filter(reference=reference).exists():
        return JsonResponse({'status': 'error', 'message': 'Ya hay otro pago con esta referencia!'}, status=400)


    if form.is_valid():
        pago = form.save(commit=False)
        pago.sorteo = sorteo
        pago.method = 'P'  # 'P' para Pago Móvil por defecto
        pago.state = 'E'   # 'E' para En Espera por defecto
        #TODO generar aquí si es necesario,el serial del PAGO ej:
        # pago.serial = generar_un_serial_unico()
        pago.save()
        return JsonResponse({'status': 'success', 'message': '¡Pago registrado con éxito! Suerte y bendiciones!'})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
        
