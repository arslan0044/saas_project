from django import forms
from .models import Lead


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'name',
            'email',
            'phone',
            'company_name',
            'estimated_value',
            'status',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Jane Doe'}),
            'email': forms.EmailInput(attrs={'placeholder': 'jane@acme.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+1 (555) 000-0000'}),
            'company_name': forms.TextInput(attrs={'placeholder': 'e.g. Acme Corp'}),
            'estimated_value': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'}),
            'status': forms.Select(),
        }
