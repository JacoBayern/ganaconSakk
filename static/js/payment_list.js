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