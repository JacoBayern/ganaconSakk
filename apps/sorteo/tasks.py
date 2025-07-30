from celery import shared_task
import logging
from .models import Payment
from .services import get_payment_status_api

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)  # Reintenta 3 veces con 1 min de espera si falla
def check_payment_status(self, payment_id):
    """
    Tarea de Celery para verificar el estado de un pago individual contra la API.
    """
    try:
        payment = Payment.objects.get(pk=payment_id, state='E')
    except Payment.DoesNotExist:
        logger.warning(f"Intento de verificar pago {payment_id} que ya no está 'En Espera' o no existe.")
        return f"Pago {payment_id} no encontrado o ya no está pendiente."

    logger.info(f"Ejecutando tarea de verificación para el pago {payment_id}")
    api_status, _ = get_payment_status_api(payment)

    if api_status == True:
        logger.info(f"API confirmó pago {payment_id}. Procesando la creación de boletos.")
        success = payment.process_verified_payment()
        if success:
            payment.state = 'V'
            payment.save(update_fields=['state'])
            return f"Pago {payment_id} verificado y procesado exitosamente."
        else:
            logger.error(f"Falló el procesamiento del pago {payment_id} (ej. sorteo lleno). Marcando como Cancelado.")
            payment.state = 'C'
            payment.save(update_fields=['state'])
            return f"Fallo al procesar el pago {payment_id}."

    elif api_status == 'REJECTED':
        logger.warning(f"API rechazó el pago {payment_id}. Marcando como Cancelado.")
        payment.state = 'C'
        payment.save(update_fields=['state'])
        return f"Pago {payment_id} rechazado por la API."

    elif api_status == 'ERROR':
        logger.error(f"Error de comunicación con la API para el pago {payment_id}. Reintentando...")
        raise self.retry()

    return f"El pago {payment_id} sigue pendiente. Estado API: {api_status}"


@shared_task
def schedule_pending_payment_checks():
    """
    Tarea periódica que encola verificaciones para todos los pagos pendientes.
    """
    pending_payments = Payment.objects.filter(state='E')
    logger.info(f"Planificador: Encontrados {pending_payments.count()} pagos pendientes. Encolando tareas de verificación.")
    for payment in pending_payments:
        check_payment_status.delay(payment.id)
    return f"Encoladas {pending_payments.count()} verificaciones de pago."