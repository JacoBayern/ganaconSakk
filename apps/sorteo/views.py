from django.shortcuts import redirect, render, get_object_or_404
from .models import Sorteo, Payment, Ticket
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .forms import PaymentForm
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, Value
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.messages import error, success
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

@login_required
def payment_list(request):
    """
    List all payments with search and pagination.
    """
    query = request.GET.get('q', '')
    state_filter = request.GET.get('state', '')

    # Ordenar por estado: 'En Espera' primero, luego el resto por fecha.
    payment_list = Payment.objects.annotate(
        state_order=Case(
            When(state='E', then=Value(1)),
            When(state='V', then=Value(2)),
            When(state='C', then=Value(3)),
            default=Value(4)
        )
    ).order_by('state_order', 'created_at')

    # Aplicar filtro de estado si se proporciona uno
    if state_filter and state_filter in ['E', 'V', 'C']:
        payment_list = payment_list.filter(state=state_filter)
    
    if query:
        payment_list = payment_list.filter(
            Q(owner_name__icontains=query) |
            Q(owner_ci__icontains=query) |
            Q(owner_email__icontains=query) |
            Q(reference__icontains=query) |
            Q(serial__icontains=query)
        )

    paginator = Paginator(payment_list, 15)  # Muestra 15 pagos por página
    page_number = request.GET.get('page')
    payments_page = paginator.get_page(page_number)

    context = {
        'payments': payments_page,
        'query': query,
        'state_filter': state_filter,
    }

    return render(request, 'payment/payment_list.html', context)

def login(request):
    """                 
    Login view
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('payment_list')
    else:
        form = AuthenticationForm()
    return render(request, 'administration/login.html', {'form': form})

@login_required
@require_http_methods(["POST"])
def verify_payment(request, payment_id):
    """
    Verify a payment
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    result = payment.process_verified_payment()
    if result:
        return JsonResponse({'status': 'success', 'message': 'Pago verificado y boletos creados exitosamente!'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Error al verificar el pago.'}, status=500)

    
@require_http_methods(["POST"])
def find_my_tickets(request):
    """
    Finds tickets by owner's CI or email.
    """
    identifier = request.POST.get('identifier', '').strip()

    if not identifier:
        return JsonResponse({'status': 'error', 'message': 'Por favor, ingrese su correo o cédula.'}, status=400)

    tickets = Ticket.objects.filter(
        Q(owner_email__iexact=identifier) | Q(owner_ci__iexact=identifier)
    ).select_related('sorteo').order_by('-created_at')

    if not tickets.exists():
        return JsonResponse({'status': 'not_found', 'message': 'No se encontraron boletos con los datos proporcionados.'})

    tickets_data = [{
        'serial': ticket.serial,
        'sorteo_title': ticket.sorteo.title,
        'created_at': ticket.created_at.strftime('%d/%m/%Y %H:%M'),
        'owner_name': ticket.owner_name,
    } for ticket in tickets]

    return JsonResponse({'status': 'success', 'tickets': tickets_data})