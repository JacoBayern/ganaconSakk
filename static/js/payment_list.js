function verifyPayment(paymentId) {
    const button = document.querySelector(`button[onclick="verifyPayment(${paymentId})"]`);
    const csrf_token = button.getAttribute('data-csrf-token');

    Swal.fire({
        title: '¿Estás seguro?',
        text: "Vas a marcar este pago como verificado. Esta acción generará los boletos correspondientes.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sí, ¡verificar!',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/payment/${paymentId}/verify`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrf_token,
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            })
            .then(response => {
                // Obtenemos el cuerpo JSON para poder leer los mensajes de error del backend
                return response.json().then(data => ({ ok: response.ok, data }));
            })
            .then(({ ok, data }) => {
                if (ok && data.status === 'success') {
                    Swal.fire({
                        title: '¡Verificado!',
                        text: data.message,
                        icon: 'success'
                    }).then(() => {
                        window.location.reload();
                    });
                } else {
                    // Si la respuesta no es "ok" o el status es "error", lanzamos un error con el mensaje del backend
                    throw new Error(data.message || 'Ocurrió un error desconocido.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire('Error', error.message, 'error');
            });
        }
    });
}

function approveManualPayment(paymentId) {
    const button = document.querySelector(`button[onclick="approveManualPayment(${paymentId})"]`);
    const csrf_token = button.getAttribute('data-csrf-token');
    const approve_url = button.getAttribute('data-approve-url');

    Swal.fire({
        title: '¿Aprobar manualmente?',
        text: "Esta acción marcará el pago como verificado y creará los boletos. No se puede deshacer.",
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#17a2b8', // Color info de Bootstrap
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sí, ¡aprobar!',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            // Crear un formulario en memoria para enviar la petición POST
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = approve_url;

            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = csrf_token;
            form.appendChild(csrfInput);

            document.body.appendChild(form);
            form.submit();
        }
    });
}