document.addEventListener("DOMContentLoaded", function() {
    const termsModalElement = document.getElementById('termsModal');
    if (!termsModalElement) {
        return; // No hacer nada si el modal no está en la página
    }

    const termsModal = new bootstrap.Modal(termsModalElement);
    const acceptBtn = document.getElementById('acceptTermsBtn');

    // Verificar si los términos ya han sido aceptados
    const hasAcceptedTerms = localStorage.getItem('termsAccepted');

    if (!hasAcceptedTerms) {
        // Si no han sido aceptados, mostrar el modal
        termsModal.show();
    }

    // Manejar el clic en el botón de aceptar
    acceptBtn.addEventListener('click', function() {
        // Guardar en localStorage que los términos han sido aceptados
        localStorage.setItem('termsAccepted', 'true');
        termsModal.hide();
    });
});