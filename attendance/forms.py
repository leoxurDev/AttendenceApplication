from django import forms
from .models import Student, ClassroomOption, AvatarEmoji, AvatarColor


class StudentForm(forms.ModelForm):
    classroom = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    avatar_emoji = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    avatar_color = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'classroom', 'avatar_emoji', 'avatar_color']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Leonardo'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Da Vinci'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate classroom choices from database
        classrooms = ClassroomOption.objects.filter(is_active=True).order_by('order')
        self.fields['classroom'].choices = [
            (c.name, c.display_value) for c in classrooms
        ]
        
        # Populate avatar emoji choices from database
        emojis = AvatarEmoji.objects.filter(is_active=True).order_by('order')
        self.fields['avatar_emoji'].choices = [
            (e.emoji, f"{e.emoji} {e.name}") for e in emojis
        ]
        
        # Populate avatar color choices from database
        colors = AvatarColor.objects.filter(is_active=True).order_by('order')
        self.fields['avatar_color'].choices = [
            (c.hex_code, f"{c.name} ({c.hex_code})") for c in colors
        ]


