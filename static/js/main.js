document.addEventListener("DOMContentLoaded", function () {
  // Configuración inicial
  const form = document.getElementById("paymentForm");
  const PRECIO_POR_BOLETO = parseFloat(form.dataset.ticketPrice) || 0;
  const CHECK_AVAILABILITY_URL = form.dataset.checkUrl;
  let currentStep = 1;
  const modalTitle = document.getElementById("paymentModalLabel");

  // Función para mostrar el paso actual
  function showStep(step) {
    // 1. Oculta todos los pasos
    document.querySelectorAll(".payment-step").forEach((step) => {
      step.style.display = "none";
    });

    // 2. Muestra solo el paso actual
    const activeStep = document.getElementById(`step-${step}`);
    if (activeStep) activeStep.style.display = "block";

    // 3. Actualiza los botones
    document.getElementById("prevBtn").style.display =
      step > 1 ? "block" : "none";
    document.getElementById("nextBtn").style.display =
      step < 4 ? "block" : "none";
    document.getElementById("submitBtn").style.display =
      step === 4 ? "block" : "none";
  }

  async function validateStep1() {
    const quantityInput = document.getElementById("id_tickets_quantity");
    const errorDiv = document.getElementById("error-tickets_quantity");
    const quantity = parseInt(quantityInput.value);

    // 1. Validación del lado del cliente (rápida)
    if (!quantity || quantity <= 0) {
      quantityInput.classList.add("is-invalid");
      errorDiv.textContent = "Ingrese una cantidad válida";
      return false; // Falla la validación
    }
    quantityInput.classList.remove("is-invalid");
    errorDiv.textContent = "";

    // 2. Validación del lado del servidor (disponibilidad)
    try {
      // Construimos la URL con la cantidad como parámetro
      const url = `${CHECK_AVAILABILITY_URL}?quantity=${quantity}`;
      const response = await fetch(url);
      const data = await response.json();

      if (data.available) {
        // Si el servidor dice que está disponible, la validación es exitosa
        return true;
      } else {
        // Si no está disponible, mostramos el mensaje del servidor
        quantityInput.classList.add("is-invalid");
        errorDiv.textContent = data.message || "No hay suficientes boletos disponibles.";
        return false; // Falla la validación
      }
    } catch (error) {
      console.error("Error al verificar disponibilidad:", error);
      quantityInput.classList.add("is-invalid");
      errorDiv.textContent = "No se pudo verificar la disponibilidad. Intente de nuevo.";
      return false; // Falla la validación por error de red
    }
  }

  // Validación del paso 2
  function validateStep2() {
    let isValid = true;
    const fields = {
      owner_name: {
        input: document.getElementById("id_owner_name"),
        msg: "Por favor, ingrese un nombre válido (ej: Juan Gonzales).",
      },
      owner_ci: {
        input: document.getElementById("id_owner_ci"),
        msg: "Por favor, ingrese su cédula.",
      },
      owner_email: {
        input: document.getElementById("id_owner_email"),
        msg: "Por favor, ingrese un correo válido.",
      },
      owner_phone: {
        input: document.getElementById("id_owner_phone"),
        msg: "Use un formato válido (ej: 04121234567).",
      },
    };

    for (const fieldName in fields) {
      const field = fields[fieldName];
      const errorDiv = document.getElementById(`error-${fieldName}`);
      field.input.classList.remove("is-invalid");
      errorDiv.textContent = "";

      let fieldIsInvalid = false;
      let customMessage = field.msg;
      if (!field.input.value.trim()) {
        fieldIsInvalid = true;
      } else if (fieldName === "owner_email") {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(field.input.value)) fieldIsInvalid = true;
      } else if (fieldName === "owner_phone") {
        // Valida los prefijos 0412, 0422, 0414, 0424, 0416, 0426 seguidos de 7 dígitos
        const phoneRegex = /^(0412|0422|0414|0424|0416|0426)\d{7}$/;
        if (!phoneRegex.test(field.input.value)) fieldIsInvalid = true;
      } else if (fieldName === "owner_ci") {
        type_CI = document.querySelector('[name="type_CI"]')?.value;
        if (type_CI === "V" || type_CI === "E") {
          const ciRegex = /^\d{7,8}$/;
          if (!ciRegex.test(field.input.value)) {
            fieldIsInvalid = true;
            customMessage =
              "La cédula ingresada debe tener entre 7 y 8 dígitos.";
          }
        } else {
          const ciRegex = /^\d{10}$/;
          if (!ciRegex.test(field.input.value)) {
            fieldIsInvalid = true;
            customMessage = "El RIF ingresado debe tener 10 dígitos.";
          }
        }
      } else if (fieldName === "owner_name") {
        const nameRegex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/;
        if (!nameRegex.test(field.input.value)) fieldIsInvalid = true;
      }

      if (fieldIsInvalid) {
        field.input.classList.add("is-invalid");
        errorDiv.textContent = customMessage;
        isValid = false;
      }
    }
    return isValid;
  }

  // Validación del paso 4 (antes paso 3)
  function validateStep4() {
    let isValid = true;
    const fields = {
      bank_of_transfer: {
        input: document.getElementById("id_bank_of_transfer"),
        msg: "Seleccione el banco desde donde transfirió.",
      },
      reference: {
        input: document.getElementById("id_reference"),
        msg: "Ingrese el número de referencia.",
      },
      transferred_date: {
        input: document.getElementById("id_transferred_date"),
        msg: "Seleccione la fecha de la transferencia.",
      },
      transferred_amount: {
        input: document.getElementById("id_transferred_amount"),
        msg: "Ingrese el monto transferido.",
      },
    };

    for (const fieldName in fields) {
      const field = fields[fieldName];
      const errorDiv = document.getElementById(`error-${fieldName}`);
      field.input.classList.remove("is-invalid");
      errorDiv.textContent = "";

      if (!field.input.value.trim()) {
        field.input.classList.add("is-invalid");
        errorDiv.textContent = field.msg;
        isValid = false;
      }
    }
    return isValid;
  }

  // Evento para el botón Siguiente
  document.getElementById("nextBtn").addEventListener("click", async function () {
    // Usamos 'await' para esperar el resultado de la validación del paso 1
    if (currentStep === 1 && !(await validateStep1())) {
        return; // Si validateStep1 devuelve false, detenemos la ejecución
    }
    if (currentStep === 2 && !validateStep2()) return;
    
    // Si la validación pasó, continuamos
    currentStep++;
    showStep(currentStep);

    if (currentStep === 3) {
      const quantity = document.getElementById("id_tickets_quantity").value;
      const total = (quantity * PRECIO_POR_BOLETO).toFixed(2);
      document.getElementById("montoPagar").textContent = `Bs.${total}`;
    }
    if (currentStep === 4) {
      const quantity = document.getElementById("id_tickets_quantity").value;
      const total = (quantity * PRECIO_POR_BOLETO).toFixed(2);
      document.getElementById("id_transferred_amount").value = total;
    }
  });

  // Evento para el botón Anterior
  document.getElementById("prevBtn").addEventListener("click", function () {
    currentStep--;
    showStep(currentStep);
  });

  // Evento para el botón Finalizar (submit)
  form.addEventListener("submit", function (e) {
    e.preventDefault();

    if (currentStep === 4 && !validateStep4()) return;

    const submitBtn = document.getElementById("submitBtn");
    submitBtn.disabled = true;
    submitBtn.innerHTML =
      '<span class="spinner-border spinner-border-sm"></span> Procesando...';

    const formData = new FormData(form);

    fetch(form.action, {
      method: "POST",
      body: formData,
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then((response) => response.json())
      .then((data) => {
        document
          .querySelectorAll(".invalid-feedback")
          .forEach((el) => (el.textContent = ""));
        document
          .querySelectorAll(".form-control")
          .forEach((el) => el.classList.remove("is-invalid"));
        if (data.status === "success") {
          form.style.display = "none";
          document.querySelector(".modal-footer").style.display = "none";
          modalTitle.textContent = "¡Éxito!";
          const finalMessage = document.getElementById("final-message");
          finalMessage.className = ""; // Limpia clases previas (ej. alert-danger)

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
                fieldInput.classList.add("is-invalid");
                errorDiv.textContent = data.errors[field][0];
              }
            }
          } else if (data.message) {
            // Muestra un error general si no es de un campo específico
            const finalMessage = document.getElementById("final-message");
            finalMessage.className = "alert alert-danger";
            finalMessage.textContent = data.message;
          }
        }
      })
      .catch((error) => console.error("Error:", error))
      .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = "Finalizar Compra";
      });
  });

  showStep(1);
});
