from django import forms
from .models import Payment, Sorteo

class PaymentForm(forms.ModelForm):
    """
    Formulario para registrar un pago.
    """
    # Se define explícitamente el campo de fecha para asegurar el formato correcto.
    # El widget `DateInput` con `type='date'` renderiza el selector de fecha nativo del navegador.
    # `input_formats` le dice a Django cómo interpretar la fecha que viene del formulario.
    transferred_date = forms.DateField(
        label="Fecha de transferencia",
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control' # Se añade la clase directamente aquí
            }
        ),
        input_formats=['%Y-%m-%d']
    )

    def __init__(self, *args, **kwargs):
        # Extraemos 'sorteo' de los kwargs para usarlo en las validaciones.
        # Esto permite que la vista pase el objeto sorteo al formulario.
        self.sorteo = kwargs.pop('sorteo', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        Sobrescribimos el método clean para añadir validaciones personalizadas
        que dependen de múltiples campos o de lógica de negocio externa (como el estado del sorteo).
        """
        cleaned_data = super().clean()

        # 1. Validación: El sorteo debe estar activo.
        if self.sorteo and self.sorteo.state != 'A':
            # Este error no está asociado a un campo específico, por lo que se mostrará como un error general.
            raise forms.ValidationError("Lo sentimos, este sorteo ya no está disponible para la compra.")

        # 2. Validación: El monto transferido debe coincidir con la cantidad de boletos.
        transferred_amount = cleaned_data.get('transferred_amount')
        tickets_quantity = cleaned_data.get('tickets_quantity')

        if self.sorteo and transferred_amount is not None and tickets_quantity is not None:
            expected_amount = self.sorteo.ticket_price * tickets_quantity
            if transferred_amount != expected_amount:
                # Asociamos el error al campo 'transferred_amount' para que se muestre junto a él.
                self.add_error('transferred_amount', 'El monto transferido no coincide con el precio y la cantidad de boletos seleccionados.')

        # 3. Validación: El número de referencia no debe estar duplicado.
        reference = cleaned_data.get('reference')
        if reference and Payment.objects.filter(reference=reference).exists():
            self.add_error('reference', 'Este número de referencia ya ha sido registrado en otro pago.')

    class Meta:
        model = Payment
        fields = [
            'tickets_quantity', 'owner_name', 'owner_ci', 'owner_email',
            'owner_phone', 'type_CI', 'bank_of_transfer', 'reference',
            'transferred_date', 'transferred_amount'
        ]
        widgets = {
            'owner_phone': forms.TextInput(attrs={'placeholder': '+584121234567'}),
        }

class SorteoForm(forms.ModelForm):
    class Meta:
        model = Sorteo
        fields = '__all__'