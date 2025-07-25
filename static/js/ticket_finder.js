document.addEventListener('DOMContentLoaded', function() {
    const findTicketsForm = document.getElementById('findTicketsForm');
    const ticketResultsContainer = document.getElementById('ticketResults');
    const findTicketsModal = document.getElementById('findTicketsModal');

    if (!findTicketsForm) return;

    findTicketsForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const submitBtn = findTicketsForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Buscando...';
        ticketResultsContainer.innerHTML = ''; // Limpiar resultados anteriores

        const formData = new FormData(findTicketsForm);

        fetch(findTicketsForm.action, {
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
                let resultsHtml = `<h5>Boletos Encontrados para ${data.tickets[0].owner_name}:</h5><ul class="list-group">`;
                data.tickets.forEach(ticket => {
                    resultsHtml += `
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <strong class="d-block">Sorteo: ${ticket.sorteo_title}</strong>
                                <small class="text-muted">Comprado el: ${ticket.created_at}</small>
                            </div>
                            <span class="badge bg-success rounded-pill fs-6">Boleto #${ticket.serial}</span>
                        </li>
                    `;
                });
                resultsHtml += '</ul>';
                ticketResultsContainer.innerHTML = resultsHtml;
            } else {
                // Maneja los estados 'not_found' y 'error'
                ticketResultsContainer.innerHTML = `<div class="alert alert-warning text-center">${data.message}</div>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            ticketResultsContainer.innerHTML = '<div class="alert alert-danger text-center">Ocurrió un error inesperado. Por favor, intente de nuevo.</div>';
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        });
    });

    // Opcional: Limpiar los resultados cuando se cierra el modal para una mejor UX
    if (findTicketsModal) {
        findTicketsModal.addEventListener('hidden.bs.modal', function () {
            ticketResultsContainer.innerHTML = '';
            findTicketsForm.reset();
        });
    }
});
