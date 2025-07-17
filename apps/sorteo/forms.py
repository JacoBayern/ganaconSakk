from django import forms
from .models import Payment

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'tickets_quantity',
            'owner_name',
            'owner_ci',
            'owner_email',
            'owner_phone',
            'reference' 
        ]
        
    widgets = {
            'tickets_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'owner_name': forms.TextInput(attrs={'class': 'form-control'}),
            'owner_ci': forms.TextInput(attrs={'class': 'form-control'}),
            'owner_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'owner_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
        }