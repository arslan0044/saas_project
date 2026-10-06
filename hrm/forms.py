from django import forms
from .models import Department, Employee


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Engineering, Sales, HR'}),
        }


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'first_name',
            'last_name',
            'email',
            'department',
            'designation',
            'joining_date',
            'salary',
            'is_active',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'employee@company.com'}),
            'department': forms.Select(),
            'designation': forms.TextInput(attrs={'placeholder': 'e.g. Senior Software Engineer'}),
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'salary': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'}),
            'is_active': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Empty department choice label
        if 'department' in self.fields:
            self.fields['department'].empty_label = "Select Department (Optional)"
