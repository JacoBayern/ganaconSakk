function verifyPayment(paymentId) {
    const button = document.querySelector(`button[onclick="verifyPayment(${paymentId})"]`);
    if (confirm('¿Estás seguro de que deseas verificar este pago?')) {
        // Usa la URL con el nuevo patrón
        const csrf_token = button.getAttribute('data-csrf-token');
        fetch(`/payment/${paymentId}/verify`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrf_token,
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                console.log('SEXOOOO: ', response)
                throw new Error('Error en la respuesta del servidor');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                alert(data.message);
                window.location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ocurrió un error al verificar el pago: ' + error.message);
        });
    }
}