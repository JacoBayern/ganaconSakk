from celery import shared_task
import logging
from .models import Payment
from .services import get_payment_status_api

_logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)  # Reintenta 3 veces con 1 min de espera si falla
def check_payment_status(self, payment_id):
    """
    Tarea de Celery para verificar el estado de un pago individual contra la API.
    """
    try:
        payment = Payment.objects.get(pk=payment_id, state='E')
    except Payment.DoesNotExist:
        _logger.warning(f"Intento de verificar pago {payment_id} que ya no está 'En Espera' o no existe.")
        return f"Pago {payment_id} no encontrado o ya no está pendiente."

    _logger.info(f"Ejecutando tarea de verificación para el pago {payment_id}")
    response = get_payment_status_api(payment)
    data = response.get('Mensaje')
    description = response.get('description')
    if data == 'Ok':
        _logger.info(f"API confirmó la verificación del pago.")
        match description:
            case 'APROBADO':
                success = payment.create_tickets()
                if success:
                    payment.state = 'V'
                    payment.save(update_fields=['state'])
                    return f"Pago {payment_id} verificado y procesado exitosamente."
                else:
                    _logger.error(f"Error al crear tickets parta el pago verificado {payment_id}.")                      
            case 'RECHAZADO':
                 # Si el pago es rechazado, marcarlo como cancelado
                payment.state = 'C'  # Cancelado
                payment.payment_verification_note(f"Pago rechazado: {description}")
                payment.save(update_fields=['state', 'payment_verification_note'])
                _logger.warning(f"Pago {self.id} rechazado: {description}")
                return False
            case 'EN PROCESO':
                payment.state = 'E'  # En Espera
                payment.payment_verification_note(f"Pago En proceso de verificación: {description}")
                payment.save(update_fields=['state', 'payment_verification_note'])
                _logger.info(f"Pago {self.id} en proceso de verificación: {description}")
                return False
                
    return True


@shared_task
def schedule_pending_payment_checks():
    """
    Tarea periódica que encola verificaciones para todos los pagos pendientes.
    """
    pending_payments = Payment.objects.filter(state='E')
    _logger.info(f"Planificador: Encontrados {pending_payments.count()} pagos pendientes. Encolando tareas de verificación.")
    for payment in pending_payments:
        check_payment_status.delay(payment.id)
    return f"Encoladas {pending_payments.count()} verificaciones de pago."