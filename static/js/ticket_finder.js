document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('findTicketsForm');
    const resultsDiv = document.getElementById('ticketResults');
    
    if (!form) return;

    const submitButton = form.querySelector('button[type="submit"]');

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        const originalButtonText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Buscando...';
        resultsDiv.innerHTML = ''; // Limpiar resultados anteriores

        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                let ticketsHTML = '<h4 class="mb-3">Tus Boletos Encontrados</h4>';
                ticketsHTML += '<ul class="list-group">';
                data.tickets.forEach(ticket => {
                    ticketsHTML += `
                        <li class="list-group-item">
                            <div class="d-flex w-100 justify-content-between">
                                <h5 class="mb-1">Boleto #${ticket.serial}</h5>
                                <small class="text-muted">${ticket.created_at}</small>
                            </div>
                            <p class="mb-1"><strong>Sorteo:</strong> ${ticket.sorteo_title}</p>
                            <small><strong>Comprador:</strong> ${ticket.owner_name}</small>
                        </li>
                    `;
                });
                ticketsHTML += '</ul>';
                resultsDiv.innerHTML = ticketsHTML;
            } else {
                resultsDiv.innerHTML = `<div class="alert alert-warning" role="alert">${data.message}</div>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            resultsDiv.innerHTML = '<div class="alert alert-danger" role="alert">Ocurrió un error al realizar la búsqueda. Por favor, inténtalo de nuevo.</div>';
        })
        .finally(() => {
            submitButton.disabled = false;
            submitButton.innerHTML = originalButtonText;
        });
    });
});