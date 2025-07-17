document.addEventListener('DOMContentLoaded', function() {
    // Configuración inicial
    const form = document.getElementById('paymentForm');
    const PRECIO_POR_BOLETO = parseFloat(form.dataset.ticketPrice) || 0;
    let currentStep = 1;
    const modalTitle = document.getElementById('paymentModalLabel');
    
    // Función para mostrar el paso actual
    function showStep(step) {
        // 1. Oculta todos los pasos
        document.querySelectorAll('.payment-step').forEach(step => {
            step.style.display = 'none';
        });
        
        // 2. Muestra solo el paso actual
        const activeStep = document.getElementById(`step-${step}`);
        if (activeStep) activeStep.style.display = 'block';
        
        // 3. Actualiza los botones
        document.getElementById('prevBtn').style.display = step > 1 ? 'block' : 'none';
        document.getElementById('nextBtn').style.display = step < 3 ? 'block' : 'none';
        document.getElementById('submitBtn').style.display = step === 3 ? 'block' : 'none';
    }
    
    // Validación del paso 1
    function validateStep1() {
        const quantityInput = document.getElementById('id_tickets_quantity');
        if (!quantityInput.value || parseInt(quantityInput.value) <= 0) {
            console.log(PRECIO_POR_BOLETO)
            quantityInput.classList.add('is-invalid');
            document.getElementById('error-tickets_quantity').textContent = 'Ingrese una cantidad válida';
            return false;
        }
        quantityInput.classList.remove('is-invalid');
        return true;
    }
    
    // Evento para el botón Siguiente
    document.getElementById('nextBtn').addEventListener('click', function() {
        if (currentStep === 1 && !validateStep1()) return;
        
        currentStep++;
        showStep(currentStep);
        
        // Calcula el monto al llegar al paso 3
        if (currentStep === 3) {
            const quantity = document.getElementById('id_tickets_quantity').value;
            const total = (quantity * PRECIO_POR_BOLETO).toFixed(2);
            document.getElementById('montoPagar').textContent = `$${total}`;
        }
    });
    
    // Evento para el botón Anterior
    document.getElementById('prevBtn').addEventListener('click', function() {
        currentStep--;
        showStep(currentStep);
    });
    
    // Evento para el botón Finalizar (submit)
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Procesando...';
        
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(response => response.json())
        .then(data => {
            document.querySelectorAll('.invalid-feedback').forEach(el => el.textContent = '');
            document.querySelectorAll('.form-control').forEach(el => el.classList.remove('is-invalid'));
            if (data.status === 'success') {
                form.style.display = 'none';
                document.querySelector('.modal-footer').style.display = 'none';
                modalTitle.textContent = "¡Éxito!";
                const finalMessage = document.getElementById('final-message');
                finalMessage.className = 'alert alert-success';
                finalMessage.innerHTML = data.message + '<p class="mt-2">Puedes cerrar esta ventana.</p>';
                // Opcional: recargar la página para ver el progreso actualizado
                setTimeout(() => window.location.reload(), 4000);
            } else {
                // Muestra los errores junto a cada campo
                if (data.errors) {
                    for (const field in data.errors) {
                        const errorDiv = document.getElementById(`error-${field}`);
                        const fieldInput = document.getElementById(`id_${field}`);
                        if (errorDiv && fieldInput) {
                            fieldInput.classList.add('is-invalid');
                            errorDiv.textContent = data.errors[field][0];
                        }
                    }
                } else if(data.message) {
                    // Muestra un error general si no es de un campo específico
                    const finalMessage = document.getElementById('final-message');
                    finalMessage.className = 'alert alert-danger';
                    finalMessage.textContent = data.message;
                }
            }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Finalizar Compra';
        });
    });
    
    // Inicializa mostrando el primer paso
    showStep(1);
    
    // Debug: Verifica que los elementos existen
    console.log('Elementos:', {
        nextBtn: document.getElementById('nextBtn'),
        prevBtn: document.getElementById('prevBtn'),
        steps: document.querySelectorAll('.payment-step')
    });
});