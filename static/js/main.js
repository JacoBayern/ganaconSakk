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
        document.getElementById('nextBtn').style.display = step < 4 ? 'block' : 'none';
        document.getElementById('submitBtn').style.display = step === 4 ? 'block' : 'none';
    }
    
    // Validación del paso 1
    function validateStep1() {
        const quantityInput = document.getElementById('id_tickets_quantity');
        if (!quantityInput.value || parseInt(quantityInput.value) <= 0) {
            quantityInput.classList.add('is-invalid');
            document.getElementById('error-tickets_quantity').textContent = 'Ingrese una cantidad válida';
            return false;
        }
        quantityInput.classList.remove('is-invalid');
        return true;
    }
    
    // Validación del paso 2
    function validateStep2() {
        let isValid = true;
        const fields = {
            'owner_name': { input: document.getElementById('id_owner_name'), msg: 'Por favor, ingrese un nombre válido (ej: Juan Gonzales).' },
            'owner_ci': { input: document.getElementById('id_owner_ci'), msg: 'Por favor, ingrese su cédula.' },
            'owner_email': { input: document.getElementById('id_owner_email'), msg: 'Por favor, ingrese un correo válido.' },
            'owner_phone': { input: document.getElementById('id_owner_phone'), msg: 'Use un formato válido (ej: 04121234567).' }
        };

        for (const fieldName in fields) {
            const field = fields[fieldName];
            const errorDiv = document.getElementById(`error-${fieldName}`);
            field.input.classList.remove('is-invalid');
            errorDiv.textContent = '';

            let fieldIsInvalid = false;
            if (!field.input.value.trim()) {
                fieldIsInvalid = true;
            } else if (fieldName === 'owner_email') {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(field.input.value)) fieldIsInvalid = true;
            } else if (fieldName === 'owner_phone') {
                // Valida los prefijos 0412, 0422, 0414, 0424, 0416, 0426 seguidos de 7 dígitos
                const phoneRegex = /^(0412|0422|0414|0424|0416|0426)\d{7}$/;
                if (!phoneRegex.test(field.input.value)) fieldIsInvalid = true;
            } else if (fieldName === 'owner_ci'){
                // Valida que la cédula sea un número de 7 a 8 dígitos
                const ciRegex = /^\d{7,8}$/;
                if (!ciRegex.test(field.input.value)) fieldIsInvalid = true;
            }else if (fieldName === 'owner_name'){
                const nameRegex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/;
                if (!nameRegex.test(field.input.value)) fieldIsInvalid = true;
            }               



            if (fieldIsInvalid) {
                field.input.classList.add('is-invalid');
                errorDiv.textContent = field.msg;
                isValid = false;
            }
        }
        return isValid;
    }

    // Validación del paso 4 (antes paso 3)
    function validateStep4() {
        let isValid = true;
        const fields = {
            'bank_of_transfer': { input: document.getElementById('id_bank_of_transfer'), msg: 'Seleccione el banco desde donde transfirió.' },
            'reference': { input: document.getElementById('id_reference'), msg: 'Ingrese el número de referencia.' },
            'transferred_date': { input: document.getElementById('id_transferred_date'), msg: 'Seleccione la fecha de la transferencia.' },
            'transferred_amount': { input: document.getElementById('id_transferred_amount'), msg: 'Ingrese el monto transferido.' }
        };

        for (const fieldName in fields) {
            const field = fields[fieldName];
            const errorDiv = document.getElementById(`error-${fieldName}`);
            field.input.classList.remove('is-invalid');
            errorDiv.textContent = '';

            if (!field.input.value.trim()) {
                field.input.classList.add('is-invalid');
                errorDiv.textContent = field.msg;
                isValid = false;
            }
        }
        return isValid;
    }

    // Evento para el botón Siguiente
    document.getElementById('nextBtn').addEventListener('click', function() {
        if (currentStep === 1 && !validateStep1()) return;
        if (currentStep === 2 && !validateStep2()) return;
        
        currentStep++;
        showStep(currentStep);
        
        // Muestra el monto a pagar en el paso 3
        if (currentStep === 3) {
            const quantity = document.getElementById('id_tickets_quantity').value;
            const total = (quantity * PRECIO_POR_BOLETO).toFixed(2);
            document.getElementById('montoPagar').textContent = `Bs.${total}`;
        }
        // Rellena el monto a pagar en el paso 4 para facilitar al usuario
        if (currentStep === 4) {
            const quantity = document.getElementById('id_tickets_quantity').value;
            const total = (quantity * PRECIO_POR_BOLETO).toFixed(2);
            document.getElementById('id_transferred_amount').value = total;
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

        if (currentStep === 4 && !validateStep4()) return;

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
                finalMessage.className = ''; // Limpia clases previas (ej. alert-danger)

                const animationHTML = `
                    <div class="success-animation">
                        <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                            <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
                            <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                        </svg>
                    </div>
                `;

                const messageHTML = `
                    <div class="alert alert-success text-center mt-3">
                        <strong>${data.message}</strong>
                        <p class="mt-2 mb-0">Puedes cerrar esta ventana.</p>
                    </div>
                `;

                finalMessage.innerHTML = animationHTML + messageHTML;
                // Opcional: recargar la página para ver el progreso actualizado
                setTimeout(() => window.location.reload(), 10000);
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
    
    showStep(1);
});