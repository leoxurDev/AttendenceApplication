from django import forms
from .models import Student

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'classroom', 'avatar_emoji', 'avatar_color']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Leo'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Lion'}),
            'classroom': forms.Select(attrs={'class': 'form-select'}),
            'avatar_emoji': forms.Select(attrs={'class': 'form-select'}),
            'avatar_color': forms.Select(attrs={'class': 'form-select'}),
        }
