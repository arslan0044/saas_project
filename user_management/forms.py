from django import forms
from django.contrib.auth.models import User
from .models import TenantUserProfile


class TenantUserProfileForm(forms.ModelForm):
    class Meta:
        model = TenantUserProfile
        fields = ['role', 'phone']
        widgets = {
            'role': forms.Select(),
            'phone': forms.TextInput(attrs={'placeholder': '+1 (555) 000-0000'}),
        }


class InviteUserForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'username'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'user@company.com'})
    )
    first_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Last Name'})
    )
    role = forms.ChoiceField(
        choices=TenantUserProfile.ROLE_CHOICES,
        widget=forms.Select()
    )
    phone = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'placeholder': '+1 (555) 000-0000'})
    )
