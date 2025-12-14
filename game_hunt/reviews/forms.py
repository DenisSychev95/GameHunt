from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['title', 'text', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Заголовок обзора'}),
            'text': forms.Textarea(attrs={'rows': 6}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 10}),
        }