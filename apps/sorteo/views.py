from django.shortcuts import redirect, render, get_object_or_404
from .models import Sorteo, Payment, Ticket
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .forms import PaymentForm, SorteoForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Case, When, Value
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging
from .services import register_payment_api

_logger = logging.getLogger()

def home(request):
    sorteo_principal = Sorteo.objects.filter(is_main=True).first()

    # Obtener la lista de otros sorteos y paginarla
    otros_sorteos_list = Sorteo.objects.exclude(is_main=True).filter(state__in=['A', 'F']).order_by('-date_lottery')
    paginator = Paginator(otros_sorteos_list, 6) # 6 sorteos por página
    page_number = request.GET.get('page')
    otros_sorteos_page = paginator.get_page(page_number)

    porcentaje_vendido = sorteo_principal.percentage_sold() if sorteo_principal else 0
    context ={
        'sorteo_principal': sorteo_principal,
        'otros_sorteos': otros_sorteos_page,
        'porcentaje_vendido': porcentaje_vendido
    }
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

@require_http_methods(["POST"])
def create_payment(request, sorteo_id):
    #TODO verificacion de numero telefonico
    #TODO verificacion de cédula de identidad
    try:
        sorteo = Sorteo.objects.get(pk=sorteo_id)
    except Sorteo.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Sorteo no disponible o no encontrado!'})

    # Se pasa la instancia del sorteo al formulario para realizar validaciones complejas.
    form = PaymentForm(request.POST, sorteo=sorteo)

    if form.is_valid():
        try:
            pago = form.save(commit=False)
            pago.sorteo = sorteo
            pago.method = 'P'  # 'P' para Pago Móvil por defecto
            pago.state = 'E'   # 'E' para En Espera por defecto¿
            pago.save()

            result, message = pago.process_verified_payment()
            _logger.warning(f"Pago creado: {pago.id}, estado: {pago.state}, mensaje: {message}")
            if not result:
                return JsonResponse({'status': 'error', 'message': message}, status=500)
            else:
                return JsonResponse({'status': 'success', 'message': '¡Pago registrado con éxito! Suerte y bendiciones! En breve podrá verificar sus tickets en el apartado "Ver mis tickets comprados"'})
        except Exception as e:
            _logger.error(f"Error al crear el pago: {e}")
    else:
        # El formulario ahora se encarga de todas las validaciones y devuelve los errores.
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required
def payment_list(request):
    """
    List all payments with search and pagination.
    """
    query = request.GET.get('q', '')
    state_filter = request.GET.get('state', '')

    # Ordenar por estado: 'En Espera' primero, luego el resto por fecha.
    payment_list = Payment.objects.select_related('sorteo').annotate(
        state_order=Case(
            When(state='E', then=Value(1)),
            When(state='V', then=Value(2)),
            When(state='C', then=Value(3)),
            default=Value(4)
        )).order_by('state_order', 'created_at')

    # Aplicar filtro de estado si se proporciona uno
    if state_filter and state_filter in ['E', 'V', 'C']:
        payment_list = payment_list.filter(state=state_filter)
    
    if query:
        print(f"Buscando: {query}")  # Debug
        payment_list = payment_list.filter(
            Q(owner_name__icontains=query) |
            Q(owner_ci__icontains=query) |
            Q(owner_email__icontains=query) |
            Q(reference__icontains=query) |
            Q(serial__icontains=query) |
            Q(sorteo__title__icontains=query)
        )
        from django.db import connection
        print(connection.queries[-1]['sql'])  # Debug SQL

    paginator = Paginator(payment_list, 15)
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

def logout_view(request):
    """
    Logout view
    """
    auth_logout(request)
    return redirect('home')


@login_required
@require_http_methods(["POST"])
def verify_payment(request, payment_id):
    """
    Verify a payment
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    result = payment.process_verified_payment()
    _logger.warning(f'RESULTADOOOO: {result}')
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

@login_required
def sorteo_list(request):
    """
    Lista todos los sorteos con búsqueda, filtro y paginación.
    """
    query = request.GET.get('q', '')
    state_filter = request.GET.get('state', '')

    sorteo_list = Sorteo.objects.all().order_by('-is_main', '-date_lottery')

    if state_filter:
        sorteo_list = sorteo_list.filter(state=state_filter)

    if query:
        sorteo_list = sorteo_list.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    paginator = Paginator(sorteo_list, 10)  # 10 sorteos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'sorteos': page_obj,
        'query': query,
        'state_filter': state_filter,
        'states': Sorteo.ESTATE,
    }
    return render(request, 'sorteo/sorteo_list.html', context)

@login_required
def ticket_list(request, sorteo_id):
    """
    Lista los tickets de un sorteo específico, con búsqueda y paginación.
    """
    query = request.GET.get('q', '')

    sorteo = get_object_or_404(Sorteo, pk=sorteo_id)

    ticket_list = Ticket.objects.filter(sorteo=sorteo).order_by('serial')

    if query:
        ticket_list = ticket_list.filter(
            Q(owner_name__icontains=query) |
            Q(owner_ci__icontains=query) |
            Q(owner_email__icontains=query) |
            Q(serial__iexact=query)
        )

    paginator = Paginator(ticket_list, 20) # 20 tickets por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'sorteo': sorteo,
        'tickets': page_obj,
        'query': query,
    }
    return render(request, 'ticket/ticket_list.html', context)

@login_required
def sorteo_edit(request, sorteo_id=None):
    """
    Crea o edita un sorteo.
    """
    if sorteo_id:
        # Editar un sorteo existente
        instance = get_object_or_404(Sorteo, pk=sorteo_id)
        page_title = f'Editando Sorteo: {instance.title}'
    else:
        # Crear un nuevo sorteo
        instance = None
        page_title = 'Crear Nuevo Sorteo'

    if request.method == 'POST':
        form = SorteoForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            sorteo = form.save()
            messages.success(request, f'Sorteo "{sorteo.title}" guardado exitosamente.')
            return redirect('sorteo_list')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = SorteoForm(instance=instance)

    context = {'form': form, 'page_title': page_title}
    return render(request, 'sorteo/sorteo_form.html', context)

def check_availability(request, sorteo_id):
    # Solo respondemos a solicitudes GET
    if request.method == 'GET':
        # Obtenemos el sorteo o devolvemos un error 404 si no existe
        sorteo = get_object_or_404(Sorteo, id=sorteo_id)
        
        # Obtenemos la cantidad que el usuario quiere comprar desde los parámetros de la URL
        try:
            quantity_wanted = int(request.GET.get('quantity', 0))
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Cantidad inválida.'}, status=400)

        if quantity_wanted <= 0:
            return JsonResponse({'available': False, 'message': 'La cantidad debe ser mayor a cero.'})

        # --- Lógica de cálculo de disponibilidad ---
        # Suponiendo que tienes un campo 'total_tickets' en tu modelo Sorteo
        total_tickets_in_raffle = sorteo.total_tickets 
        
        # Suponiendo que cada ticket vendido es un objeto en el modelo Ticket
        tickets_sold = Ticket.objects.filter(sorteo=sorteo).count()
        
        available_tickets = total_tickets_in_raffle - tickets_sold
        
        if quantity_wanted <= available_tickets:
            # Hay suficientes boletos
            return JsonResponse({'available': True})
        else:
            # No hay suficientes boletos
            message = f'Lo sentimos, solo quedan {available_tickets} boletos disponibles.'
            if available_tickets == 0:
                message = '¡Lo sentimos, todos los boletos se han agotado!'
            return JsonResponse({'available': False, 'message': message})
            
    # Si no es GET, devolvemos un error de método no permitido
    return JsonResponse({'error': 'Método no permitido'}, status=405)