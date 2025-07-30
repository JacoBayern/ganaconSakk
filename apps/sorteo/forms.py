from django import forms
from .models import Payment, Sorteo

class SorteoForm(forms.ModelForm):
    class Meta:
        model = Sorteo
        fields = [
            'title', 'description', 'date_lottery', 'prize_picture', 
            'ticket_price', 'total_tickets', 'state', 'is_main', 
            'lottery_conditions'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date_lottery': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'prize_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'ticket_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_tickets': forms.NumberInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-select'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'lottery_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'tickets_quantity',
            'owner_name',
            'type_CI',
            'owner_ci',
            'owner_email',
            'owner_phone',
            'bank_of_transfer',
            'reference',
            'transferred_amount',
            'transferred_date',
        ]
        
        widgets = {
            'tickets_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'owner_name': forms.TextInput(attrs={'class': 'form-control'}),
            'type_CI': forms.Select(attrs={'class': 'form-select'}),
            'owner_ci': forms.TextInput(attrs={'class': 'form-control'}),
            'owner_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'owner_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_of_transfer': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'transferred_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'transferred_date': forms.DateInput(
                attrs={'class': 'form-control', 'placeholder': 'DD/MM/YYYY', 'type': 'date'},
                format='%d/%m/%Y'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['transferred_date'].input_formats = ('%d/%m/%Y',)