import requests
import logging
from django.conf import settings
import os

_logger = logging.getLogger(__name__)


def register_payment_api(payment):
    """
    Registra un pago en la API externa.
    Retorna (True, data) en caso de éxito, o (False, error_dict) en caso de fallo.
    """
    url = os.getenv('ADD_PAYMENT_URL')
    token = os.getenv('TOKEN_KEY')
    id_usr = os.getenv('ID_USR')
    tlf = '0'+str(payment.owner_phone.national_number)
    payload = {
        'idusr': id_usr,
        'token': token,
        'idPago': payment.serial,
        'mtPago': '{0:.2f}'.format(payment.transferred_amount).replace('.', ',') ,
        'descPago': f"Pago de {payment.tickets_quantity}",
        'nuReferenciaTransf': payment.reference,
        'idbancoTransf': '117',
        'fechaTransferencia': payment.transferred_date.strftime('%d/%m/%Y'),
        'nacCiTitularCuentaTransferencia': payment.type_CI,
        'numeroCiTitularCuentaTransferencia': payment.owner_ci,
        'nmTitularCuentaTransferencia': payment.owner_name,
        'telfTitularCuentaTransferencia': tlf,
        'correoTitularCuentaTransferencia': payment.owner_email,
    }
    headers = {'Content-Type': 'application/json'}
    _logger.warning(f'Registrando pago: {payload}')
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        data = response.json()

        mensaje = data.get('Mensaje')

        respuesta_json = {
        "codigo_respuesta": mensaje,
        "descripcion": "",
        }

        match mensaje:
            case "PAGO_INGRESADO":
                respuesta_json["descripcion"] = "El pago fue registrado, iniciando proceso de verificación."
            case "IDPAGO_YA_REGISTRADO":
                respuesta_json["descripcion"] = "Ya existe un pago registrado con ese ID."
            case "TRANSFERENCIA_YA_REGISTRADA":
                respuesta_json["descripcion"] = "Este número de referencia ya fue utilizado en otra transacción."
            case "IDBANCO_TRANSFERENCIA_INCORRECTO":
                respuesta_json["descripcion"] = "El banco no coincide con los bancos registrados."
            case "USUARIO_NO_VALIDO":
                respuesta_json["descripcion"] = "El usuario proporcionado no es válido."
            case "IDPAGO_ES_OBLIGATORIO":
                respuesta_json["descripcion"] = "Debe indicar el ID del pago."
            case "MONTO_ES_OBLIGATORIO":
                respuesta_json["descripcion"] = "Debe indicar el monto del pago."
            case "MONTO_NO_VALIDO":
                respuesta_json["descripcion"] = "El monto proporcionado no es válido."
            case "DESCRIPCION_PAGO_ES_OBLIGATORIO":
                respuesta_json["descripcion"] = "La descripción del pago es obligatoria."
            case "NUREFERENCIA_ES_OBLIGATORIO":
                respuesta_json["descripcion"] = "El número de referencia es obligatorio."
            case "IDBANCO_ES_OBLIGATORIO":
                respuesta_json["descripcion"] = "Debe indicar el banco de la transferencia."
            case "IDBANCO_NO_VALIDO":
                respuesta_json["descripcion"] = "ID de banco inválido."
            case "FECHA_TRANSFERENCIA_ES_OBLIGATORIA":
                respuesta_json["descripcion"] = "Debe indicar la fecha de la transferencia."
            case "FECHA_TRANSFERENCIA_NO_VALIDA":
                respuesta_json["descripcion"] = "La fecha indicada no es válida."
            case "NAC_TITULAR_ES_OBLIGATORIA":
                respuesta_json["descripcion"] = "Debe indicar la nacionalidad del titular."
            case "NUM_CEDULA_ES_OBLIGATORIA":
                respuesta_json["descripcion"] = "Debe indicar el número de cédula."
            case "NUM_CEDULA_NO_VALIDO":
                respuesta_json["descripcion"] = "El número de cédula es inválido."
            case "NOMBRE_TIT_ES_OBLIGATORIA":
                respuesta_json["descripcion"] = "El nombre del titular es obligatorio."
            case "TELF_TIT_ES_OBLIGATORIA":
                respuesta_json["descripcion"] = "El número telefónico del titular es obligatorio."
            case "CORREO_TIT_ES_OBLIGATORIA":
                respuesta_json["descripcion"] = "Debe indicar un correo electrónico del titular."
            case "ERROR_INTERNO":
                respuesta_json["descripcion"] = "Se produjo un error interno en la plataforma."
            case _:
                respuesta_json["descripcion"] = "Mensaje de error desconocido."

        return True, respuesta_json
    except requests.exceptions.RequestException as e:
        _logger.error(f"Error al registrar el pago {payment.id} en la API: {e}")
        return False, {'message': str(e)}

def get_payment_status_api(payment):
    """
    Consulta el estado de un pago en la API externa.
    Retorna el estado (ej: 'VERIFIED', 'REJECTED') y los datos de la API.
    """

    url = os.getenv('STATUS_PAYMENT_URL')
    token = os.getenv('TOKEN_KEY')
    id_usr = os.getenv('ID_USR')

    payload = {
        'idusr': id_usr,
        'token': token,
        'idPago': payment.serial
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        data = response.json()
        mensaje = data.get('Mensaje')
        estatus = data.get('estatus')
        respuesta_json = {
        "codigo_respuesta": mensaje,
        "descripcion": "",
        "estatus": estatus,
        }

        match mensaje:
            case 'USUARIO_NO_VALIDO':
                respuesta_json["descripcion"] = 'El usuario proporcionado no es válido.'
            case 'ID_PAGO_NO_REGISTRADO': 
                respuesta_json["descripcion"] = 'El ID del pago no está registrado.'
            case 'OK':
                estatus = data.get('estatus')
                match estatus:
                    case 'APROBADO':
                        respuesta_json["descripcion"] = 'El pago ha sido aprobado.'                        
                    case 'RECHAZADO':
                        causaRechazo = data.get('causaRechazo')
                        respuesta_json["descripcion"] = f'El pago ha sido rechazado: {causaRechazo}'
                    case 'EN PROCESO':
                        respuesta_json["descripcion"] = 'El pago está en proceso de ser verificado.'
                    

        
        _logger.info(f"Consulta de estado para pago {payment.id}: API devolvió '{mensaje} {respuesta_json['descripcion']}'")
        return respuesta_json
    except requests.exceptions.RequestException as e:
        _logger.error(f"Error al consultar estado del pago {payment.id} en la API: {e}")
        return 'ERROR', {'message': str(e)}
